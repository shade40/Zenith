import time
from typing import Callable

from pytermgui import tim, parse
from cleur.markup import markup

TARGETS = [
    "[bold limegreen]This is [italic]some [cyan] basic [/] markup",
    # "[bold]This has one [!gradient(60)]macro",
    # "[!upper italic]This has some [!shuffle !rainbow]macros",
]

RUN_COUNT = 1000


def benchmark(parse: Callable) -> None:
    tim.print(f"[secondary bold]{parse.__qualname__}:")

    for target in TARGETS:
        start = time.perf_counter_ns()

        try:
            for i in range(RUN_COUNT):
                result = parse(target)

        except Exception as exc:
            tim.print(f"    [bold error]FAIL [/]at i={i}: {exc}")
            continue

        elapsed = time.perf_counter_ns() - start
        print(f"    {round(elapsed / RUN_COUNT, 4)} ns - {result}")

    print()


def main() -> None:
    for parser in (tim.parse, parse, markup):
        benchmark(parser)


if __name__ == "__main__":
    main()
