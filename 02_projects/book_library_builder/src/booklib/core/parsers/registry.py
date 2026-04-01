from pathlib import Path

from .epub import EPUBParser


PARSERS = {
    ".epub": EPUBParser(),
}


def get_parser(ext):

    return PARSERS.get(ext.lower())


def get_parser_for_path(path):

    return get_parser(Path(path).suffix)
