import time

from carmine import Carmine
from zenith import zml

TEST_STRINGS = [
    "[bold 141]Simple test",
    "[bold 141]Simple test [/fg]with an unsetter",
    "[!upper]Single macro",
    "[!upper]Single macro [/!upper]with an unsetter",
    "[!upper !gradient(zenith)]Multiple macros",
    "[!upper !gradient(zenith)]Multiple macros [/]with an unsetter",
]


def command() -> None:
    """My Carmine project."""


def zprint(markup: str) -> None:
    """Prints some ZML."""

    print(zml(markup))


def _benchmark(markup: str, count: int) -> tuple[float, float, float]:
    """Evaluates the markup `count` times, returns the average time it took."""

    times = []

    for _ in range(count):
        start = time.perf_counter_ns()
        zml(markup)
        times.append(time.perf_counter_ns() - start)

    return max(times), min(times), sum(times) / len(times)


def command_measure(count: int = 1000) -> None:
    """Measures the average amount of time it took to parse a list of markup.

    Args:
        count: How many times to run to get an average.
    """

    for markup in TEST_STRINGS:
        zprint(f"Testing: '{markup}[/]'")

        maximum, minimum, average = _benchmark(markup, count)
        zprint(f"--> [bold]max[/]: {maximum:.2f}ns[/]")
        zprint(f"    [bold]min[/]: {minimum:.2f}ns[/]")
        zprint(f"    [bold]avg[/]: {average:.2f}ns[/]\n")


def main(argv: list[str] | None = None) -> None:
    """Runs the application."""

    with Carmine(argv) as cli:
        cli += command

        cli += command_measure


if __name__ == "__main__":
    import sys

    main(sys.argv)
