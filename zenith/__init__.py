import sys
from typing import TextIO

from . import exceptions, macros, markup, palette
from .exceptions import *
from .markup import *
from .palette import *

__all__ = [
    *exceptions.__all__,
    *markup.__all__,
    *palette.__all__,
    "macros",
    "zprint",
]


def zprint(
    *items: str,
    sep: str = " ",
    end: str = "\x1b[0m\n",
    file: TextIO = sys.stdout,
    flush: bool = False
) -> None:
    """Mimicks built-in print, but parses each item as ZML."""

    parsed = [zml(item) for item in items]

    print(*parsed, sep=sep, end=end, file=file, flush=flush)
