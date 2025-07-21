import json
import re
import unittest
import os

from poste_italiane_parser import get_parser


def list_tests():
    """
    Lists all test cases in the current module.
    """
    test_dir = os.path.dirname(__file__)
    return [
        os.path.join(test_dir, f)
        for f in os.listdir(test_dir)
        if f != "example.test.json" and f.endswith(".test.json")
    ]


class TestPIExtractor(unittest.TestCase):
    def test_all(self):
        tests = list_tests()

        if not tests:
            self.fail("No test cases found.")

        for test_file_path in tests:
            with open(test_file_path, "r") as f:
                with self.subTest(
                    msg=f"Testing file: {os.path.basename(test_file_path)}"
                ):
                    test_result = json.loads(f.read())

                    provider = get_parser(test_result["path"])

                    currency = provider.currency()
                    self.assertEqual(currency, test_result["currency"])

                    generated_at = provider.generated_at()
                    self.assertEqual(generated_at, test_result["generated_at"])

                    if "account_number" in test_result and (
                        test_result["account_number"] is not None
                        and test_result["account_number"] != ""
                    ):
                        account_number = provider.account_number()
                        self.assertEqual(account_number, test_result["account_number"])

                    period = provider.period()
                    self.assertEqual(
                        period["start_date"], test_result["period_start_date"]
                    )
                    self.assertEqual(period["end_date"], test_result["period_end_date"])

                    customer = provider.customer()
                    self.assertEqual(customer["name"], test_result["customer_name"])
                    if "street" in customer and (
                        customer["street"] is not None and customer["street"] != ""
                    ):
                        self.assertEqual(
                            customer["street"], test_result["customer_street"]
                        )
                    if "city" in customer and (
                        customer["city"] is not None and customer["city"] != ""
                    ):
                        self.assertEqual(customer["city"], test_result["customer_city"])

                    holder = provider.holder()
                    self.assertEqual(holder, test_result["holder"])

                    if "initial_balance" in test_result and (
                        test_result["initial_balance"] is not None
                        and test_result["initial_balance"] != ""
                    ):
                        initial_balance = provider.initial_balance()
                        self.assertEqual(
                            initial_balance, (test_result["initial_balance"])
                        )

                    if "final_balance" in test_result and (
                        test_result["final_balance"] is not None
                        and test_result["final_balance"] != ""
                    ):
                        final_balance = provider.final_balance()
                        self.assertEqual(final_balance, (test_result["final_balance"]))

                    if "card_number" in test_result and (
                        test_result["card_number"] is not None
                        and test_result["card_number"] != ""
                    ):
                        card_number = provider.card_number()
                        self.assertEqual(card_number, test_result["card_number"])

                    if "iban" in test_result and (
                        test_result["iban"] is not None and test_result["iban"] != ""
                    ):
                        iban = provider.iban()
                        self.assertEqual(iban, test_result["iban"])

                    # test transactions if are present
                    if "transactions" in test_result:
                        for transaction in test_result["transactions"]:
                            found = False
                            for t in provider.transactions():
                                for key in transaction:
                                    if key not in t or t[key] != transaction[key]:
                                        break
                                else:
                                    found = True
                                    break

                            self.assertTrue(
                                found,
                                f"Transaction {transaction} not found in provider transactions.",
                            )
