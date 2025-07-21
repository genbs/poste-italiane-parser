import re

from poste_italiane_parser.base_parser import BaseParser
from poste_italiane_parser.utils.pdf import parse_text_in_area


class RendicontoParser(BaseParser):
    def __init__(self, path):
        super().__init__(
            name="RENDICONTO",
            path=path,
            parsing_config={
                "columns": {
                    "data": [46, 100],
                    "valuta": [110, 160],
                    "addebiti": [220, 250],
                    "accrediti": [280, 330],
                    "operazione": [338, 580],
                },
                "page_area": [0, 130, -1, 726],
                "first_page_area": [0, 300, -1, 726],
                "holder_area": [365, 85, 500, 96],
                "generated_at_area": [400, 47, 460, 60],
                "customer_area": [290, 180, 510, 220],
                "card_number_area": [358, 74, 480, 85],
                "iban_area": [77, 134, 240, 145],
            },
        )

    def parse(self):
        return super().parse()

    @staticmethod
    def check(path):
        """
        Checks if the PDF file at the given path is valid for this provider.
        """
        if not BaseParser.check(path):
            return False

        area = [300, 70, 600, 80]
        account_regex = re.compile(r"\*{12}\d{4}")  # card number
        text = parse_text_in_area(path, area)

        return account_regex.search(text) if text else False
