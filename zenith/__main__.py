from __future__ import annotations

from argparse import ArgumentParser

from .markup import zml


def command_zml(argv: list[str] | None = None) -> None:
    """Parses arguments for the ZML parser command."""

    parser = ArgumentParser(description="The ZML CLI interface.")

    parser.add_argument("markup", help="The markup to be parsed.")
    parser.add_argument(
        "-e", "--escape", help="Prints the output escaped.", action="store_true"
    )

    args = parser.parse_args(argv)

    output = zml(args.markup)

    if args.escape:
        print(repr(output))
    else:
        print(output)
