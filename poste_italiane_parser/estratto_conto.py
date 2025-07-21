import re

from poste_italiane_parser.base_parser import BaseParser
from utils.pdf import parse_text_in_area


class EstrattoContoParser(BaseParser):
    def __init__(self, path):
        super().__init__(
            name="ESTRATTO_CONTO",
            path=path,
            parsing_config={
                "columns": {
                    "data": [70, 75],
                    "valuta": [120, 125],
                    "addebiti": [210, 230],
                    "accrediti": [300, 320],
                    "operazione": [360, 600],
                },
                "page_area": [0, 100, -1, 800],
                "first_page_area": [0, 300, -1, 800],
                "holder_area": [360, 82, 500, 94],
                "currency_area": [390, 68, 420, 82],
                "generated_at_area": [390, 40, 430, 50],
                "customer_area": [290, 180, 510, 220],
                "account_number_area": [150, 200, 220, 220],
                "iban_area": [36, 160, 240, 168],
            },
        )

    @staticmethod
    def check(path):
        """
        To determine if the given PDF is a Bancoposta Estratto Conto,
        we check if it is a valid PDF and if it contains an account number.
        """
        if not BaseParser.check(path):
            return False

        area = [150, 200, 220, 220]
        account_regex = re.compile(r"\d{1,14}")  # account number
        text = parse_text_in_area(path, area)

        return account_regex.search(text) if text else False
