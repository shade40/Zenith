import pytest
from gunmetal import Span

from zenith.markup import alias, define, markup, markup_spans


def test_markup_str_parse():
    def _upper(text: str) -> str:
        return text.upper()

    define("!upper", _upper)

    assert (
        markup("[bold underline 61]Hello [141 /bold]There")
        == "\x1b[38;5;61;1;4mHello \x1b[22m\x1b[38;5;141mThere\x1b[0m"
    )

    assert markup("[38]Hello [!upper]There") == "\x1b[38;5;38mHello THERE\x1b[0m"

    assert markup(
        "Click [141 underline ~https://google.com]me[61] and me[/~ / bold red] NOW"
    ) == (
        "Click \x1b]8;;https://google.com\x1b\\\x1b[38;5;141;4mme"
        + "\x1b]8;;https://google.com\x1b\\\x1b[38;5;61m and me\x1b[0m"
        + "\x1b]8;;\x1b\\\x1b[38;2;255;0;0;1m NOW\x1b[0m"
    )

    assert markup("The never-ending [~https://google.com]URI") == (
        "The never-ending \x1b]8;;https://google.com\x1b\\URI\x1b]8;;\x1b\\"
    ), repr(markup("The never-ending [~https://google.com]URI"))

    assert markup("[blue][@red]This is hard to parse") == (
        "\x1b[38;2;0;0;255;48;2;255;0;0mThis is hard to parse\x1b[0m"
    )


def test_markup_parse():
    assert list(markup_spans("[bold italic]Hello")) == [
        Span("Hello", bold=True, italic=True),
    ]

    assert list(markup_spans("[bold italic]Hello[/bold]Not bold")) == [
        Span("Hello", bold=True, italic=True),
        Span("Not bold", italic=True),
    ]


def test_markup_color():
    # 0-7 indexed colors
    assert list(markup_spans("[@0 1]Test[@1 0]Other")) == [
        Span("Test", background="40", foreground="31"),
        Span("Other", background="41", foreground="30"),
    ]

    # 8-15 indexed colors
    assert list(markup_spans("[@9 15]Test[@14 10]Other")) == [
        Span("Test", background="101", foreground="97"),
        Span("Other", background="106", foreground="92"),
    ]

    # 16-256 indexed colors
    assert list(markup_spans("[@141 61]Test[@54 78]Other")) == [
        Span("Test", background="48;5;141", foreground="38;5;61"),
        Span("Other", background="48;5;54", foreground="38;5;78"),
    ]

    # OOB indexed color
    with pytest.raises(ValueError):
        list(markup_spans("[@333 231]Please don't parse..."))

    # CSS colors
    assert list(markup_spans("[@lavender cadetblue]Pretty colors")) == [
        Span(
            "Pretty colors", foreground="38;2;95;158;160", background="48;2;230;230;250"
        )
    ]

    # HEX colors
    assert list(markup_spans("[@#212121 #dedede]Nice contrast")) == [
        Span("Nice contrast", foreground="38;2;222;222;222", background="48;2;33;33;33")
    ]

    # RGB colors
    assert list(markup_spans("[@11;22;123 123;22;11]What even are these colors")) == [
        Span(
            "What even are these colors",
            foreground="38;2;123;22;11",
            background="48;2;11;22;123",
        )
    ]


def test_markup_auto_foreground():
    assert list(markup_spans("[@#FFFFFF]test")) == [
        Span("test", background="48;2;255;255;255", foreground="38;2;35;35;35")
    ]

    assert list(markup_spans("[@0]White[@7]Black[@160]White[@116]Black")) == [
        Span("White", background="40", foreground="38;2;245;245;245"),
        Span("Black", background="47", foreground="38;2;35;35;35"),
        Span("White", background="48;5;160", foreground="38;2;245;245;245"),
        Span("Black", background="48;5;116", foreground="38;2;35;35;35"),
    ]


def test_markup_macros():
    def _upper(text: str) -> str:
        return text.upper()

    def _conceal(text: str) -> str:
        return "*" * (len(text) - 1) + text[-1]

    define("!upper", _upper)
    define("!conceal", _conceal)

    assert list(
        markup_spans("[!upper 141]Test[/!upper /fg !conceal bold]other test")
    ) == [
        Span("TEST", foreground="38;5;141"),
        Span("*********t", bold=True),
    ]

    with pytest.raises(ValueError):
        list(markup_spans("[!undefined]Test"))

    with pytest.raises(ValueError):
        list(markup_spans("[undefined]Test"))

    with pytest.raises(ValueError):
        list(markup_spans("[/!upper]Test"))


def test_markup_aliases():
    alias(a="b", test="141 bold")

    assert list(markup_spans("[test italic]What is this?")) == [
        Span("What is this?", italic=True, bold=True, foreground="38;5;141")
    ]

    def _upper(text: str) -> str:
        return text.upper()

    define("!upper", _upper)

    alias(complex_with_macro="!upper lavender")

    assert list(markup_spans("[complex-with-macro]test")) == [
        Span("TEST", foreground="38;2;230;230;250")
    ]

    alias(complex_with_hyperlink="~https://google.com underline slategray")

    assert list(markup_spans("[complex-with-hyperlink]test")) == [
        Span(
            "test",
            underline=True,
            hyperlink="https://google.com",
            foreground="38;2;112;128;144",
        )
    ]


def test_markup_hyperlink():
    assert list(
        markup_spans("[~https://google.com]Test [bold]me [/~]no more link")
    ) == [
        Span("Test ", hyperlink="https://google.com"),
        Span("me ", bold=True, hyperlink="https://google.com"),
        Span("no more link", bold=True),
    ]


def test_markup_parse_plain():
    assert list(markup_spans("Test")) == [Span("Test")]
