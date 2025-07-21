from poste_italiane_parser.base_parser import BaseParser
from utils.pdf import parse_text_in_area


class ListaMovimentiParser(BaseParser):
    def __init__(self, path):
        super().__init__(
            name="LISTA_MOVIMENTI",
            path=path,
            parsing_config={
                "columns": {
                    "data": [80, 100],
                    "valuta": [130, 160],
                    "operazione": [170, 490],
                    "addebiti": [480, 510],
                    "accrediti": [540, 600],
                },
                "page_area": [0, 69, -1, 800],
                "first_page_area": [0, 238, -1, 800],
                "holder_area": [120, 154, 400, 168],
                "generated_at_area": [400, 77, 550, 90],
                "customer_area": [125, 152, 280, 158],
                "card_number_area": [120, 140, 220, 160],
                "iban_area": [240, 140, 380, 160],
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

        return parse_text_in_area(path, [40, 60, 200, 100]) == "SALDO E MOVIMENTI"
