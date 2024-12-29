from __future__ import annotations

import re
from functools import lru_cache
from typing import Callable, Literal, TypedDict

from slate.color import Color
from slate.color_info import NAMED_COLORS
from slate.span import UNSETTERS, Span
from slate.terminal import terminal
from slate.core import ColorSpace, width as text_width

from .exceptions import ZmlNameError, ZmlSemanticsError

__all__ = [
    "zml",
    "zml_wrap",
    "zml_alias",
    "zml_escape",
    "zml_macro",
    "combine_spans",
    "zml_get_spans",
    "zml_pre_process",
    "zml_context",
    "MarkupContext",
    "MacroType",
    "GLOBAL_CONTEXT",
]

MacroType = Callable[..., str]

FULL_RESET = Span("FULL_RESET")
"""A sentinel value to be used for signifying a full style reset (CSI 0)."""

RE_MARKUP = re.compile(r"(?:\[([^\[\]]+)\])?([^\]\[]+)?")
RE_COLOR = re.compile(
    r"(?:^@?([\d]{1,3})$)|(?:@?#?([0-9a-fA-F]{6}))|(@?\d{1,3};\d{1,3};\d{1,3})"
)


class MarkupContext(TypedDict):
    """A ctx mapping that stores alias & macro information."""

    aliases: dict[str, str]
    macros: dict[str, MacroType]


# TODO: Maybe this could also implement all word boundaries except for just " "?
def zml_wrap(text: str, width: int) -> list[str]:
    """Wraps text by spaces or newlines for each line to fit in the given width.

    This method properly treats markup tags as non-displayed.
    """

    lines = []
    in_tag = False

    for line in text.splitlines():
        current = ""
        length = 0

        for char in line:
            if char == "[":
                in_tag = True

            elif char == "]":
                in_tag = False

            current += char

            if in_tag:
                continue

            length += 1

            if length == width:
                *current, rest = current.split(" ")
                lines.append(" ".join(current))

                current = rest
                length = text_width(rest)

        if current != "":
            lines.append(current)

    return lines


def zml_context() -> MarkupContext:
    """Generates an empty MarkupContext object."""

    return {"aliases": {}, "macros": {}}


GLOBAL_CONTEXT = zml_context()


def zml_macro_setter(*, ctx: MarkupContext) -> Callable[[MacroType], MacroType]:
    """Returns a decorator that will define a macro in the given context."""

    def _define(macro: MacroType) -> MacroType:
        name = macro.__name__.replace("_", "-")

        ctx["macros"][f"!{name}"] = macro

        return macro

    return _define


zml_macro = zml_macro_setter(ctx=GLOBAL_CONTEXT)
"""A macro setter for the global context."""


def _find_unsetter(tag: str) -> str:
    """Finds the unsetter for the given tag."""

    if tag.startswith("!"):
        return tag

    key = tag

    if RE_COLOR.match(tag) or tag in NAMED_COLORS:
        key = "bg" if tag.startswith("@") else "fg"

    return f"/{key}"


def zml_alias(
    *, ctx: MarkupContext | None = None, assign_unsetter: bool = True, **pairs: str
) -> None:
    """Aliases each item of the given pairs."""

    if assign_unsetter:
        for key, value in pairs.copy().items():
            pairs[f"/{key}"] = " ".join(_find_unsetter(part) for part in value.split())

    ctx = ctx or GLOBAL_CONTEXT

    aliases = ctx["aliases"]

    for key, value in pairs.items():
        aliases[key.replace("_", "-")] = value


class StyleMap(TypedDict):
    """A type to keep track of span styles."""

    bold: bool
    dim: bool
    italic: bool
    underline: bool
    blink: bool
    fast_blink: bool
    invert: bool
    conceal: bool
    strike: bool

    foreground: Color | None
    background: Color | None
    hyperlink: str


def _get_style_map() -> StyleMap:
    """Generates an empty StyleMap object."""

    return {
        "bold": False,
        "dim": False,
        "italic": False,
        "underline": False,
        "blink": False,
        "fast_blink": False,
        "invert": False,
        "conceal": False,
        "strike": False,
        "foreground": None,
        "background": None,
        "hyperlink": "",
    }


def _apply_auto_foreground(styles: StyleMap) -> bool:
    """Determines whether automatic foreground can be applied to the style map."""

    foreground = styles["foreground"]
    background = styles["background"]

    invert = styles["invert"]
    if invert:
        foreground, background = background, foreground

    if foreground is None and background is not None:
        new = background.contrast.as_background(invert)

        if invert:
            styles["background"] = new
        else:
            styles["foreground"] = new

        return True

    return False


def parse_color(color: str, background: bool | int) -> str:
    """Parses a color tag."""

    background *= 10

    color = color.lstrip("@")

    if color.isdigit():
        index = int(color)

        if 0 <= index < 8:
            return str(30 + background + index)

        if 8 <= index < 16:
            index += 2  # Skip codes 38 & 48
            return str(80 + background + index)

        if index < 256:
            return f"{38 + background};5;{index}"

        raise ZmlNameError(
            color, "Color tags should be in the range 0-255.", expected_type="color"
        )

    # Substitute named colors when possible
    color = NAMED_COLORS.get(color, color)

    if color.startswith("#"):
        color = color.lstrip("#")

        alpha = color[6:]

        color = ";".join(
            str(int(part, base=16)) for part in [color[:2], color[2:4], color[4:6]]
        )

        if alpha != "":
            color += f";{int(alpha, base=16) / 255}"

    return f"{38 + background};2;{color}"


def _apply_tag(tag: str, styles: StyleMap) -> None:
    """Applies the given tag to the style map.

    Note that this mutates the given map!
    """

    if tag == "/":
        styles.update(**_get_style_map())  # type: ignore
        return

    is_unsetter = tag.startswith("/")
    is_background = tag.startswith("@")

    tag = tag.lstrip("/").lstrip("@")

    if tag in styles or tag in ["fg", "bg"]:
        if tag == "fg":
            styles["foreground"] = None

        elif tag == "bg":
            styles["background"] = None

        else:
            styles[tag] = not is_unsetter  # type: ignore

        return

    layer: Literal["background", "foreground"] = (
        "background" if is_background else "foreground"
    )

    if RE_COLOR.match(tag):
        styles[layer] = Color.from_ansi(parse_color(tag, is_background))
        return

    if tag in NAMED_COLORS:
        styles[layer] = Color.from_hex(NAMED_COLORS[tag]).as_background(is_background)

        return

    if tag.startswith("~"):
        styles["hyperlink"] = "" if is_unsetter else tag[1:]
        return

    raise ZmlNameError(tag)


def _parse_macro(tag: str) -> tuple[str, list[str]]:
    """Parses the given macro into its name and arguments."""

    args_start = tag.find("(")

    if args_start == -1:
        return tag, []

    args = tag[args_start + 1 : -1].split(",")

    return tag[:args_start], args


def _apply_prefix(tag: str, prefix: str) -> str:
    """Applies the prefix to the given tag.

    Most importantly, this function can recognize `@tags`, and insert the prefix to the
    correct spot (between `@` and the first letter).
    """

    if tag.startswith("@"):
        return "@" + prefix + tag[1:]

    if tag.startswith("!"):
        return "!" + prefix + tag[1:]

    return prefix + tag


@lru_cache(512)
def combine_spans(spans: tuple[Span, ...]) -> str:
    """Combines the given span iterable into optimized ANSI text."""

    styles = _get_style_map()

    buff = ""
    span: Span | None = None

    for span in spans:
        if span is FULL_RESET:
            buff += "\x1b[0m"
            styles = _get_style_map()
            continue

        new = {}
        unset = []

        for key, value in span.attrs.items():
            if key in ["text", "reset_after"]:
                continue

            if key == "hyperlink" and value not in ["", styles[key]]:  # type: ignore
                new[key] = value
                continue

            if styles[key] != value:  # type: ignore
                new[key] = value

                if not value and key != "hyperlink":
                    unset.append(key)

        if len(unset) > 0:
            # TODO: Maybe this could insert into the span's sequences?
            buff += "\x1b["

            for key in unset:
                buff += UNSETTERS[key] + ";"

            buff = buff.rstrip(";") + "m"

        buff += str(Span(**new, text=span.text, reset_after=False))  # type: ignore
        styles.update(**new)  # type: ignore

    return buff


@lru_cache(512)
def zml_get_spans(text: str) -> tuple[Span, ...]:
    """Gets all spans from the given ZML text."""

    styles: StyleMap = _get_style_map()
    spans: list[Span] = []

    for mtch in RE_MARKUP.finditer(text):
        tags, plain = mtch.groups()

        # No tags or plain value, likely at the end of the string.
        if tags == plain == None:
            continue

        tags = tags or ""
        plain = plain or ""

        for tag in tags.split():
            if tag == "/":
                spans.append(FULL_RESET)

            _apply_tag(tag, styles)

        if plain == "":
            continue

        auto_fg = _apply_auto_foreground(styles)
        spans.append(Span(plain, **styles))

        if auto_fg:
            styles["foreground"] = None

    return (*spans,)


def _on_color_space_set(_: ColorSpace | None) -> bool:
    zml_get_spans.cache_clear()

    return True


terminal.on_color_space_set += _on_color_space_set


def zml_pre_process(  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    text: str, prefix: str = "", ctx: MarkupContext | None = None
) -> str:
    """Applies pre-processing to the given ZML text.

    Currently, this involves three steps:

    - Substitute all aliases with their real values
    - Evaluate macros on the plain text
    - Eliminate groups that don't contain a plain part
    """

    ctx = ctx or GLOBAL_CONTEXT

    aliased = ""

    for mtch in RE_MARKUP.finditer(text):
        tags, plain = mtch.groups()

        if tags == plain == None:
            continue

        if tags is not None:
            aliased += "["

            for tag in tags.split():
                if "*" in tag:
                    aliased += f"!alpha({','.join(tag.split('*'))}) "
                    continue

                prefixed = _apply_prefix(tag, prefix)

                if prefixed in ctx["aliases"]:
                    tag = ctx["aliases"][prefixed]

                aliased += tag + " "

            aliased = aliased.rstrip(" ") + "]"

        if plain is not None:
            aliased += plain

    text = aliased

    macros: dict[str, tuple[MacroType, list[str]]] = {}
    get_macro = ctx["macros"].get

    output = ""
    for mtch in RE_MARKUP.finditer(text):
        tags, plain = mtch.groups()

        # No tags or plain value, likely at the end of the string.
        if tags == plain == None:
            continue

        tags = tags or ""
        plain = plain or ""

        tag_list = tags.split()

        for tag in tag_list.copy():
            if tag == "/":
                macros.clear()
                continue

            if not tag.startswith(("!", "/!")):
                continue

            if tag.startswith("/!"):
                name = tag[1:]

                if name not in macros:
                    raise ZmlSemanticsError(
                        name,
                        "Cannot unset a macro when that isn't set.",
                        expected_type="macro",
                    )

                del macros[name]

            else:
                name, args = _parse_macro(tag)
                prefixed = _apply_prefix(name, prefix)
                macro = get_macro(prefixed, None)

                if macro is None:
                    raise ZmlNameError(prefixed, expected_type="macro")

                macros[name] = (macro, args)

            tag_list.remove(tag)

        if len(tag_list) > 0:
            output += f"[{' '.join(tag_list)}]"

        if plain is not None:
            for macro, args in macros.values():
                plain = macro(plain, *args)

            output += plain

    return output.replace("][", " ")


def zml_escape(text: str) -> str:
    """Escapes non-intended ZML tags."""

    return text.replace("[", r"\[").replace("]", r"\]")


def _escape(text: str, replacements: tuple[str, str]) -> str:
    """Escapes ZML-syntax characters with the given replacements."""

    return text.replace(r"\[", replacements[0]).replace(r"\]", replacements[1])


def _unescape(text: str, replacements: tuple[str, str]) -> str:
    """Escapes ZML-syntax characters with the given replacements."""

    return text.replace(replacements[0], "[").replace(replacements[1], "]")


def zml(
    markup: str,
    prefix: str = "",
    ctx: MarkupContext | None = None,
    escape_replacements: tuple[str, str] = ("{{{{", "}}}}"),
) -> str:
    """Parses ZML markup into optimized ANSI text.

    DOCUMENT THIS
    """

    markup = _escape(markup, escape_replacements)

    # TODO: This step should be cached/done smarter. It takes ages!
    markup = zml_pre_process(markup, prefix=prefix, ctx=ctx)

    return _unescape(combine_spans(zml_get_spans(markup)), escape_replacements)
