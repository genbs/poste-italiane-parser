from poste_italiane_parser.estratto_conto import EstrattoContoParser
from poste_italiane_parser.lista_movimenti import ListaMovimentiParser
from poste_italiane_parser.rendiconto import RendicontoParser


def get_parser(path):
    """
    Find the appropriate parser for the given PDF file path.
    """
    if EstrattoContoParser.check(path):
        return EstrattoContoParser(path)
    elif RendicontoParser.check(path):
        return RendicontoParser(path)
    elif ListaMovimentiParser.check(path):
        return ListaMovimentiParser(path)
    else:
        return None


def PosteItalianeParser(path):
    """
    Parse the PDF file at the given path and return the parsed data.
    """
    provider = get_parser(path)
    if not provider:
        raise ValueError(f"No provider found for file: {path}")

    return provider.parse()
