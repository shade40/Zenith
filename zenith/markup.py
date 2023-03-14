from __future__ import annotations

import re
from typing import Generator, TypedDict, Callable
from gunmetal.span import SETTERS, UNSETTERS, Span

from .color import Color
from .color_info import CSS_COLORS
from .lru_cache import LRUCache


_markup_cache = LRUCache(1024)

_full_reset = Span("FULL_RESET")
"""A sentinel value to be used for signifying a full style reset (CSI 0)."""


class ContextMapping(TypedDict):
    """A type to repersent markup contexts."""

    aliases: dict[str, str]
    macros: dict[str, Callable[[str], str]]


class StyleStack(TypedDict):
    """A type to represent span styles."""

    bold: bool
    dim: bool
    italic: bool
    underline: bool
    blink: bool
    fast_blink: bool
    invert: bool
    conceal: bool
    strike: bool

    foreground: str
    background: str
    hyperlink: str


MarkupGroup = tuple[str, list[str]]

RE_MARKUP = re.compile(r"(?:\[(.+?)\])?([^\]\[]+)(?=\[|$)")
RE_COLOR = re.compile(
    r"(?:^@?([\d]{1,3})$)|(?:@?#?([0-9a-fA-F]{6}))|(@?\d{1,3};\d{1,3};\d{1,3})"
)

GLOBAL_ALIASES: dict[str, str] = {}
GLOBAL_MACROS: dict[str, Callable[[str], str]] = {}
GLOBAL_CONTEXT: ContextMapping = {"aliases": GLOBAL_ALIASES, "macros": GLOBAL_MACROS}

BASE_STYLE_STACK = {
    "bold": False,
    "dim": False,
    "italic": False,
    "underline": False,
    "blink": False,
    "fast_blink": False,
    "invert": False,
    "conceal": False,
    "strike": False,
    "foreground": "",
    "background": "",
    "hyperlink": "",
}


def _parse_color(color: str) -> str:
    background = color.startswith("@") * 10
    color = color.lstrip("@")

    if color.isdigit():
        index = int(color)

        if 0 <= index < 8:
            return str(30 + background + index)

        if 8 <= index < 16:
            index += 2  # Skip codes 38 & 48
            return str(80 + background + index)

        elif index < 256:
            return f"{38 + background};5;{index}"

        else:
            raise ValueError(
                f"Could not parse indexed color {color!r};"
                " it should be between 0 and 16, or 16 and 255."
            )

    if color in CSS_COLORS:
        color = CSS_COLORS[color]

    if color.startswith("#"):
        color = color.lstrip("#")

        color = ";".join(
            str(int(part, base=16)) for part in [color[:2], color[2:4], color[4:]]
        )

    return f"{38 + background};2;{color}"


def _apply_auto_foreground(style_stack: dict[str, bool]) -> bool:
    """Applies contrasting foreground colors when none are set."""

    back = style_stack.get("background") or None
    fore = style_stack.get("foreground") or None

    if style_stack["invert"]:
        back, fore = fore, back

    if not (fore is None and back is not None):
        return False

    style_stack["foreground"] = Color.from_ansi(back).contrast.as_background(False).ansi
    return True


def _get_hashable_key(
    text: str, ctx: ContextMapping
) -> tuple[str, tuple[str, str | Callable[[str], str]]]:
    """Combines the given text and context into something that is hashable.

    Args:
        text: The text input into the markup function.
        ctx: The markup context.

    Returns:
        A tuple, containing all the information passed in under a hashable format.
    """

    return (
        text,
        (
            ("aliases", tuple((key, value) for key, value in ctx["aliases"].items())),
            ("macros", tuple((key, value) for key, value in ctx["macros"].items())),
        ),
    )


def markup_spans(
    text: str, ctx: ContextMapping = GLOBAL_CONTEXT
) -> Generator[Span, None, None]:
    """Generates Span objects representative of the markup text given.

    Aliases are evaluated first, followed by macros. After that, the resulting markup is
    parsed.

    Args:
        text: Some markup string.
        ctx: A context mapping to get aliases and macros from.

    Yields:
        Spans, as they occur in the markup. Each span represents a plain bit, styled by
        the current style stack.
    """

    style_stack = BASE_STYLE_STACK.copy()
    macros: list[Callable[[str], str]] = []

    get_macro = ctx["macros"].get
    get_alias = ctx["aliases"].get

    def _apply_tag(tag: str) -> None:
        """Parses and applies the given tag to the style stack.

        Args:
            tag: The markup tag to apply.
        """

        is_setter = not tag.startswith("/")
        tag = tag.lstrip("/")

        if tag == "" and not is_setter:
            style_stack.update(**BASE_STYLE_STACK)

            return

        # Style setters and color unsetters
        if tag in style_stack or tag in ["fg", "bg"]:
            if tag in ["fg", "bg"]:
                style_stack["foreground" if tag == "fg" else "background"] = ""
            else:
                style_stack[tag] = is_setter

            return

        # Colors
        if RE_COLOR.match(tag) or tag.lstrip("@") in CSS_COLORS:
            layer = "background" if tag.startswith("@") else "foreground"
            style_stack[layer] = _parse_color(tag)
            return

        # Macros
        if tag.startswith("!"):
            macro = get_macro(tag, None)

            if macro is None:
                raise ValueError(f"Undefined macro {tag!r}.")

            if not is_setter:
                try:
                    macros.remove(macro)
                except ValueError:
                    raise ValueError(
                        f"Macro {tag!r} is not set, so it can't be unset."
                    ) from None

                return

            macros.append(macro)
            return

        # Hyperlinks
        if tag.startswith("~"):
            style_stack["hyperlink"] = "" if not is_setter else tag.lstrip("~")
            return

        # Aliases
        alias = get_alias(tag, None)

        if alias is None:
            raise ValueError(f"Unknown tag {tag!r}.")

        for tag in alias.split():
            _apply_tag(tag)

    spans = []

    for mtch in RE_MARKUP.finditer(text):
        tags, plain = mtch.groups()

        if tags is None:
            tags = ""

        for tag in tags.split():
            if tag == "/":
                yield _full_reset

            _apply_tag(tag)

        for macro in macros:
            plain = macro(plain)

        should_delete_foreground = _apply_auto_foreground(style_stack)

        yield Span(plain, **style_stack)

        if should_delete_foreground:
            del style_stack["foreground"]


def parse_spans(spans: Iterable[Span]) -> str:
    """Parses spans into an optimized ANSI string.

    Args:
        spans: Any iterable of spans.

    Returns:
        The ANSI styled text the input spans represent. Optimizations are done
        in many places to reduce the output's length and noise.
    """

    style_stack: StyleStack = BASE_STYLE_STACK.copy()

    buff = ""
    hyperlink = ""

    span: Span | None = None

    for span in spans:
        if span is _full_reset:
            buff += "\x1b[0m"
            hyperlink = style_stack["hyperlink"]

            style_stack.update(**BASE_STYLE_STACK)
            style_stack["hyperlink"] = hyperlink

            continue

        stack = BASE_STYLE_STACK.copy()
        unset = []

        for key, value in span.attrs.items():
            if key not in style_stack:
                continue

            if key == "hyperlink":
                stack[key] = value

            if style_stack[key] != value:
                if value:
                    stack[key] = value

                else:
                    unset.append(key)

        if unset != []:
            if unset != ["hyperlink"]:
                buff += (
                    "\x1b["
                    + ";".join(
                        UNSETTERS.get(key) for key in unset if key != "hyperlink"
                    )
                    + "m"
                )

            if "hyperlink" in unset:
                buff += "\x1b]8;;\x1b\\"

        buff += str(span.mutate(reset_after=False, **stack)).rstrip("\x1b]8;;\x1b\\")

        style_stack.update(**stack)

    if span is not None:
        attrs = span.attrs

        if any(span.attrs[key] for key in style_stack if key != "hyperlink"):
            buff += "\x1b[0m"

        if span.hyperlink != "":
            buff += "\x1b]8;;\x1b\\"

    return buff


def markup(text: str, ctx: ContextMapping = GLOBAL_CONTEXT) -> str:
    """Parses the given markup as a string.

    Under the hood, this joins the `Span` object generated by `markup_spans`.

    Args:
        text: Some markup string.
        ctx: A context mapping to get aliases and macros from.

    Returns:
        The parsed string that is represented by the given markup.
    """

    hashable_key = _get_hashable_key(text, ctx)

    if hashable_key in _markup_cache:
        return _markup_cache[hashable_key]

    buff = parse_spans(markup_spans(text, ctx))

    _markup_cache[hashable_key] = buff

    return buff
