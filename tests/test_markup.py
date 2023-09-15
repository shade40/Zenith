import time
import pytest

from slate import terminal, ColorSpace, Color
from zenith import zml, zml_alias, zml_macro, ZmlNameError, ZmlSemanticsError
from zenith.markup import parse_color


def test_markup_builtin_only():
    assert (
        result := zml("[bold 141]Hello [@61]There ")
    ) == "\x1b[38;5;141;1mHello \x1b[48;5;61mThere ", repr(result)

    assert (
        result := zml("[bold 141]Hello [/bold @61]There ")
    ) == "\x1b[38;5;141;1mHello \x1b[22m\x1b[48;5;61mThere ", repr(result)

    assert (
        result := zml("[bold 141]Hello [/]There ")
    ) == "\x1b[38;5;141;1mHello \x1b[0mThere ", repr(result)

    assert (
        result := zml("[~https://github.com]Hello There ")
    ) == "\x1b]8;;https://github.com\x1b\\Hello There \x1b]8;;\x1b\\", repr(result)

    assert (result := zml("[~https://github.com]Hello [red]There [/~]no link")) == (
        "\x1b]8;;https://github.com\x1b\\Hello "
        + "\x1b]8;;\x1b\\\x1b[38;2;255;0;0mThere no link"
    ), repr(result)

    assert (
        result := zml("[127]Hello [/fg]There ")
    ) == "\x1b[38;5;127mHello \x1b[39mThere ", repr(result)

    assert (
        result := zml("[127]Hello [/bg]There ")
    ) == "\x1b[38;5;127mHello There ", repr(result)


def test_markup_aliases():
    zml_alias(test="brown bold")

    assert (
        result := zml("[test @red]Hello")
    ) == "\x1b[38;2;165;42;42;48;2;255;0;0;1mHello", repr(result)

    assert (
        result := zml("[test]Hello[/test]Reset")
    ) == "\x1b[38;2;165;42;42;1mHello\x1b[22;39mReset", repr(result)


def test_markup_macros():
    @zml_macro
    def epoch(template: str, fmt: str = "%c") -> str:
        return template.format(time=f"the current time with {fmt=}")

    assert (
        result := zml("[!epoch]Hello at {time}[/!epoch]{time}")
    ) == "Hello at the current time with fmt='%c'{time}", repr(result)

    assert (
        result := zml("[!epoch(%M)]Hello at {time}[/!epoch]{time}")
    ) == "Hello at the current time with fmt='%M'{time}", repr(result)

    with pytest.raises(TypeError):
        zml("[!epoch(%m,%M)]test {time}")

    @zml_macro
    def debug(template: str, *args: str) -> str:
        return template.format(args=str(args))

    assert (result := zml("[!debug(arg1,arg2)]{args}")) == "('arg1', 'arg2')", repr(
        result
    )

    assert (
        result := zml("[!debug(arg1,arg2) red bold]{args}[/fg]other: {args}")
    ) == "\x1b[38;2;255;0;0;1m('arg1', 'arg2')\x1b[39mother: ('arg1', 'arg2')", repr(
        result
    )


def test_markup_auto_foreground():
    assert (
        result := zml("[@red]Test")
    ) == "\x1b[38;2;35;35;35;48;2;255;0;0mTest", repr(result)

    assert (
        result := zml("[@black]Test")
    ) == "\x1b[38;2;245;245;245;48;2;0;0;0mTest", repr(result)

    assert (
        result := zml("[@black black]Test")
    ) == "\x1b[38;2;0;0;0;48;2;0;0;0mTest", repr(result)

    assert (
        result := zml("[@yellow]Test")
    ) == "\x1b[38;2;35;35;35;48;2;255;255;0mTest", repr(result)

    assert (
        result := zml("[invert yellow]Test")
    ) == "\x1b[38;2;255;255;0;48;2;35;35;35;7mTest", repr(result)

    assert (
        (result := zml("[@yellow]Black[@black]White"))
        == "\x1b[38;2;35;35;35;48;2;255;255;0mBlack\x1b[38;2;245;245;245;48;2;0;0;0mWhite"
    ), repr(result)


def test_markup_colors():
    assert parse_color("red", False) == "38;2;255;0;0"
    assert parse_color("blue", True) == "48;2;0;0;255"
    assert parse_color("2", False) == "32"
    assert parse_color("9", False) == "91"
    assert parse_color("14", True) == "106"
    assert parse_color("78", True) == "48;5;78"
    assert (
        parse_color("#baebae", True)
        == parse_color("186;235;174", True)
        == "48;2;186;235;174"
    )


def test_markup_parse_errors():
    with pytest.raises(ZmlNameError):
        parse_color("256", False)

    with pytest.raises(ZmlNameError):
        zml("[not-a-tag]Hello")

    with pytest.raises(ZmlNameError):
        zml("[!not-a-macro]Hello")

    with pytest.raises(ZmlSemanticsError):
        zml("Test[/!not-a-macro]")

    @zml_macro
    def not_a_macro(text: str) -> str:
        return "Why did you call this"

    with pytest.raises(ZmlSemanticsError):
        zml("Test[/!not-a-macro]")


def test_markup_downgrade_colors():
    Color.terminal = terminal

    terminal.color_space = ColorSpace.TRUE_COLOR

    assert (result := zml("[6]Test[/]")) == "\x1b[36mTest\x1b[0m", repr(result)
    assert (result := zml("[141]Test[/]")) == "\x1b[38;5;141mTest\x1b[0m", repr(result)
    assert (
        result := zml("[@#212121]Test[/]")
    ) == "\x1b[38;2;245;245;245;48;2;33;33;33mTest\x1b[0m", repr(result)

    terminal.color_space = ColorSpace.EIGHT_BIT
    assert (result := zml("[3]Test[/]")) == "\x1b[33mTest\x1b[0m", repr(result)
    assert (result := zml("[138]Test[/]")) == "\x1b[38;5;138mTest\x1b[0m", repr(result)

    assert (
        result := zml("[@#212121]Test[/]")
    ) == "\x1b[38;5;231;48;5;59mTest\x1b[0m", repr(result)

    assert (result := zml("[123;34;56]Test[/]")) == "\x1b[38;5;95mTest\x1b[0m", repr(
        result
    )

    terminal.color_space = ColorSpace.STANDARD
    assert (result := zml("[@2]Test[/]")) == "\x1b[30;42mTest\x1b[0m", repr(result)
    assert (result := zml("[#456723]Test[/]")) == "\x1b[90mTest\x1b[0m", repr(result)
    assert (result := zml("[45]Test[/]")) == "\x1b[96mTest\x1b[0m", repr(result)
