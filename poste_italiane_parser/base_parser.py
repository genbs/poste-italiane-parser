import datetime
import locale
import logging
import os
import re
from abc import ABC

from poste_italiane_parser.utils.pdf import parse_table, parse_text_in_area

logging.getLogger(__name__)

# Set the locale to Italian for date parsing
locale.setlocale(locale.LC_TIME, "it_IT.UTF-8")


class BaseParser(ABC):
    """
    This class serves as a base for all parsers, providing common functionality.
    """

    def __init__(self, name, path, parsing_config):
        if not self.check(path):
            raise ValueError(f"Invalid PDF file for parser: {path}")

        self.name = name

        self.parsing_config = parsing_config

        self.load(path)

    def load(self, path):
        self.path = path

        # get the rows from the PDF
        rows = parse_table(
            self.path,
            columns=self.parsing_config["columns"],
            page_area=self.parsing_config["page_area"],
            first_page_area=self.parsing_config["first_page_area"],
            required_columns=["data", "operazione"],
            multiple_page_rows=["operazione"],
            stop_fn=lambda value, values: value["operazione"] == "SALDO FINALE",
        )

        # map the rows to the desired format
        rows = [
            {
                "accounting_date": BaseParser._timestamp(row["data"]),
                "value_date": BaseParser._timestamp(row["valuta"]),
                "description": row["operazione"],
                "debits": BaseParser._float(row["addebiti"]),
                "credits": BaseParser._float(row["accrediti"]),
                "value": BaseParser._float(row["accrediti"])
                - BaseParser._float(row["addebiti"]),
            }
            for row in rows
        ]

        # filter by operation
        skip_operations = [
            "SALDO FINALE",
            "SALDO INIZIALE",
            "GIACENZA MEDIA NEL PERIODO",
            "TOTALE ENTRATE",
            "TOTALE USCITE",
        ]
        self.rows = [row for row in rows if row["description"] not in skip_operations]
        self.meta_rows = [row for row in rows if row["description"] in skip_operations]

        logging.debug(
            f"Parsed {len(self.rows)} rows and {len(self.meta_rows)} meta rows from {self.name}."
        )

        # validate the result of parsing
        # if not meta_rows we cannot validate the result
        # if self.meta_rows, we can sum all credits and check if "saldo finale" is equal to the sum of credits and debits
        if len(self.meta_rows) > 0:
            initial_balance = next(
                (
                    row["credits"]
                    for row in self.meta_rows
                    if row["description"] == "SALDO INIZIALE"
                ),
                None,
            )
            if not initial_balance:
                raise ValueError("Initial balance not found in the PDF.")

            final_balance = next(
                (
                    row["credits"]
                    for row in self.meta_rows
                    if row["description"] == "SALDO FINALE"
                ),
                None,
            )
            if not final_balance:
                raise ValueError("Final balance not found in the PDF.")

            calculated_total_income = sum(row["credits"] for row in self.rows)
            calculated_total_expense = sum(row["debits"] for row in self.rows)
            difference = calculated_total_income - calculated_total_expense
            expected_final_balance = round(initial_balance + difference, 4)

            if expected_final_balance != final_balance:
                raise ValueError(
                    f"Final balance mismatch: expected {expected_final_balance}, got {final_balance}"
                )

            logging.debug(
                f"Final balance matches: {expected_final_balance} == {final_balance}"
            )

            total_income = next(
                (
                    row["credits"]
                    for row in self.meta_rows
                    if row["description"] == "TOTALE ENTRATE"
                ),
                None,
            )
            total_expense = next(
                (
                    row["debits"]
                    for row in self.meta_rows
                    if row["description"] == "TOTALE USCITE"
                ),
                None,
            )

            if total_income is not None and total_expense is not None:
                logging.debug(
                    f"Total income: {total_income}, Total expense: {total_expense}, "
                    f"Calculated total income: {calculated_total_income}, "
                    f"Calculated total expense: {calculated_total_expense}"
                )

                if total_income != calculated_total_income:
                    raise ValueError(
                        f"Total income mismatch: expected {total_income}, got {calculated_total_income}"
                    )
                if total_expense != calculated_total_expense:
                    raise ValueError(
                        f"Total expense mismatch: expected {total_expense}, got {calculated_total_expense}"
                    )

    def holder(self):
        """
        Returns the holder of the account
        """
        return parse_text_in_area(self.path, self.parsing_config["holder_area"])

    def generated_at(self):
        """
        Returns the date when the document was generated.
        """
        date = parse_text_in_area(self.path, self.parsing_config["generated_at_area"])
        if not date:
            raise ValueError("Generated date not found in the PDF.")

        return BaseParser._timestamp(date)

    def customer(self):
        """
        Returns the customer information
        """
        customer = parse_text_in_area(self.path, self.parsing_config["customer_area"])

        customer = customer.split("\n")
        if len(customer) < 3:
            return {"name": customer[0].strip()}

        customer = {
            "name": customer[0].strip(),
            "street": customer[1].strip(),
            "city": customer[2].strip(),
        }

        return customer

    def currency(self):
        """
        Returns the currency of the account
        """
        if "currency_area" not in self.parsing_config:
            return "EURO"  # like in EstrattoContoParser

        curr = parse_text_in_area(self.path, self.parsing_config["currency_area"])
        if not curr:
            raise ValueError("Currency not found in the PDF.")

        return curr.strip().upper()

    def initial_balance(self):
        """
        Returns the initial balance
        """
        initial_balance = next(
            (
                row["credits"]
                for row in self.meta_rows
                if row["description"] == "SALDO INIZIALE"
            ),
            None,
        )

        return initial_balance

    def final_balance(self):
        """
        Returns the final balance
        """
        final_balance = next(
            (
                row["credits"]
                for row in self.meta_rows
                if row["description"] == "SALDO FINALE"
            ),
            None,
        )

        return final_balance

    def account_number(self):
        if "account_number_area" not in self.parsing_config:
            return None

        account = parse_text_in_area(
            self.path, self.parsing_config["account_number_area"]
        )
        if not account:
            raise ValueError("Account number not found in the PDF.")

        return account

    def card_number(self):
        """
        Returns the card number if available.
        """
        if "card_number_area" not in self.parsing_config:
            return None

        card_number = parse_text_in_area(
            self.path, self.parsing_config["card_number_area"]
        )
        if not card_number:
            return None

        # Find all characters that are digits (\d) or asterisks (\*)
        matches = re.findall(r"[\d\*]", card_number)
        return "".join(matches)

    def iban(self):
        """
        Returns the IBAN if available.
        """
        if "iban_area" not in self.parsing_config:
            return None

        iban = parse_text_in_area(self.path, self.parsing_config["iban_area"])
        return iban.strip().replace(" ", "") if iban else None

    def period(self):
        """
        Returns the period of the account
        """
        # check in the meta rows "SALDO INIZIALE" and "SALDO FINALE", if it exists, use the dates from these rows, otherwise use the first and last row of self.rows
        initial_balance_data = next(
            (
                row["accounting_date"]
                for row in self.meta_rows
                if row["description"] == "SALDO INIZIALE"
            ),
            None,
        )
        final_balance_data = next(
            (
                row["accounting_date"]
                for row in self.meta_rows
                if row["description"] == "SALDO FINALE"
            ),
            None,
        )

        if (not initial_balance_data or not final_balance_data) and not self.rows:
            return {
                "start_date": None,
                "end_date": None,
            }

        # if initial_balance_date start_date initial_balance_date else self.rows[0]["accounting_date"]
        start_date = (
            initial_balance_data
            if initial_balance_data
            else self.rows[0]["accounting_date"]
        )
        end_date = (
            final_balance_data
            if final_balance_data
            else self.rows[-1]["accounting_date"]
        )

        return {
            "start_date": start_date,
            "end_date": end_date,
        }

    def transactions(self):
        """
        Returns the parsed transactions from the PDF.
        """
        return self.rows

    def parse(self):
        """
        Parse the PDF file and return the parsed data.
        """
        return {
            "document_type": self.name,
            "currency": self.currency(),
            "account_number": self.account_number(),
            "card_number": self.card_number(),
            "iban": self.iban(),
            "customer": self.customer(),
            "holder": self.holder(),
            "generated_at": self.generated_at(),
            "initial_balance": self.initial_balance(),
            "final_balance": self.final_balance(),
            "period": self.period(),
            "transactions": self.transactions(),
        }

    @staticmethod
    def check(path):
        """
        Check if the given path is a valid PDF file for this parser.
        """
        return path.lower().endswith(".pdf") and os.path.isfile(path)

    @staticmethod
    def _float(value):
        return (
            float(value.replace("_", "").replace(".", "").replace(",", "."))
            if value
            else 0
        )

    @staticmethod
    def _timestamp(date):
        """
        Convert a date string in the format 'DD/MM/YY' or 'DD/MM/YYYY' or "DD MMMM YYYY" to a timestamp.
        """
        if not date:
            return None

        date = date.lower().strip()
        format = "%d/%m/%Y"

        if "ore" in date:  # listamovimenti
            format = "%d %B %Y ore %H:%M"
        else:
            date_parts = date.split("/")
            # if the date_parts are less than 2, there was an error in parsing

            date_parts[2] = (
                len(date_parts[2]) == 2 and f"20{date_parts[2]}" or date_parts[2]
            )
            date = "/".join(date_parts)

        try:
            date_obj = datetime.datetime.strptime(date, format).replace(
                tzinfo=datetime.timezone.utc
            )
            return date_obj.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            raise ValueError("Invalid date format.")
