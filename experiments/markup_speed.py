from timeit import timeit

from zenith import zml

EXEC_COUNT = 1000


def main() -> None:
    print(
        "Input: "
        + zml("[@black grey] ").removesuffix(" \x1b[0m")
        + "[bold 141]Hello [/fg @61]There\n"
        + "\x1b[0m",
        timeit(
            'zml("[bold 141]Hello [/fg @61]There")',
            globals=globals(),
            number=EXEC_COUNT,
        )
        * float("1e+9")
        / EXEC_COUNT,
    )


if __name__ == "__main__":
    main()
