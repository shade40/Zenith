from timeit import timeit

from zenith.markup import markup

EXEC_COUNT = 1000


def main() -> None:
    print(
        "Input: "
        + markup("[@black grey] ").removesuffix(" \x1b[0m")
        + "[bold 141]Hello [/fg @61]There\n"
        + "\x1b[0m",
        timeit(
            'markup("[bold 141]Hello [/fg @61]There")',
            globals=globals(),
            number=EXEC_COUNT,
        )
        * float("1e+9")
        / EXEC_COUNT,
    )


if __name__ == "__main__":
    main()
