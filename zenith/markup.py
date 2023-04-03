"""Zenith's markup language and its related utilities."""

from __future__ import annotations

import re
from typing import Callable, Generator, Hashable, Iterable, TypedDict, cast

from slate.span import UNSETTERS, Span

from .color import Color
from .color_info import CSS_COLORS
from .lru_cache import LRUCache

__all__ = [
    "alias",
    "define",
    "FULL_RESET",
    "parse_spans",
    "markup",
    "ContextMapping",
    "GLOBAL_CONTEXT",
]

_markup_cache = LRUCache(1024)

FULL_RESET = Span("FULL_RESET")
"""A sentinel value to be used for signifying a full style reset (CSI 0)."""


class ContextMapping(TypedDict):
    """A type to repersent markup contexts."""

    aliases: dict[str, str]
    macros: dict[str, Callable[[str], str]]

    @classmethod
    def new(cls) -> ContextMapping:
        """Creates a new context mapping."""

        return {
            "aliases": {},
            "macros": {},
        }


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

RE_MARKUP = re.compile(r"(?:\[([^\[\]]+)\])?([^\]\[]+)?")
RE_COLOR = re.compile(
    r"(?:^@?([\d]{1,3})$)|(?:@?#?([0-9a-fA-F]{6}))|(@?\d{1,3};\d{1,3};\d{1,3})"
)

GLOBAL_CONTEXT: ContextMapping = ContextMapping.new()

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


def alias(
    *,
    ctx: ContextMapping | None = None,
    keep_case: bool = False,
    **aliases: tuple[str, str],
) -> None:
    """Sets up an alias in the given context.

    Args:
        **aliases: Key=value pairs to alias, like `alias(my_alias="141", my_alias_2="61")`.
        ctx: The context to alias within. Defaults to the global context.
        keep_case: If set, alias keys won't be kebab-cased (my_alias -> my-alias).
    """

    ctx = ctx or GLOBAL_CONTEXT
    ctx_aliases = ctx["aliases"]

    for key, value in aliases.items():
        key = key if keep_case else key.replace("_", "-")

        ctx_aliases[key] = value


def define(
    identifier: str, value: Callable[[str], str], ctx: ContextMapping | None = None
) -> None:
    """Defines a markup macro within the given context.

    Args:
        identifier: The name the macro can be referenced by. Must start with '!'.
        value: The callback that is executed by the macro. This takes the partially
            parsed output at the moment the macro is found, and returns some
            modification of it.
        ctx: The context to alias within. Defaults to the global context.
    """

    if not identifier.startswith("!"):
        raise ValueError(
            "Macro identifiers must start with `!`, {identifier!r} doesn't."
        )

    ctx = ctx or GLOBAL_CONTEXT
    ctx["macros"][identifier] = value


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

        if index < 256:
            return f"{38 + background};5;{index}"

        raise ValueError(
            f"Could not parse indexed color {color!r};"
            " it should be between 0 and 16, or 16 and 255."
        )

    # Substitute CSS's named colors when possible
    color = CSS_COLORS.get(color, color)

    if color.startswith("#"):
        color = color.lstrip("#")

        color = ";".join(
            str(int(part, base=16)) for part in [color[:2], color[2:4], color[4:]]
        )

    return f"{38 + background};2;{color}"


def _apply_auto_foreground(style_stack: dict[str, bool | str]) -> bool:
    """Applies contrasting foreground colors when none are set."""

    back = style_stack.get("background") or None
    fore = style_stack.get("foreground") or None

    if style_stack["invert"]:
        back, fore = fore, back

    if not (fore is None and back is not None):
        return False

    assert isinstance(back, str)

    style_stack["foreground"] = Color.from_ansi(back).contrast.as_background(False).ansi
    return True


def _get_hashable_key(text: str, ctx: ContextMapping, prefix: str) -> Hashable:
    """Combines the given text and context into something that is hashable.

    Args:
        text: The text input into the markup function.
        ctx: The markup context.
        prefix: The prefix used for looking up aliases and macros.

    Returns:
        A tuple, containing all the information passed in under a hashable format.
    """

    return (
        text,
        (
            ("aliases", tuple((key, value) for key, value in ctx["aliases"].items())),
            ("macros", tuple((key, value) for key, value in ctx["macros"].items())),
        ),
        prefix,
    )


def markup_spans(
    text: str, ctx: ContextMapping | None = None, prefix: str = ""
) -> Generator[Span, None, None]:
    """Generates Span objects representative of the markup text given.

    Aliases are evaluated first, followed by macros. After that, the resulting markup is
    parsed.

    Args:
        text: Some markup string.
        ctx: A context mapping to get aliases and macros from. Defaults to the global
            context.
        prefix: The prefix to apply when looking up aliases and macros. Use this to
            compartmentalize markup aliases to each user library.

    Yields:
        Spans, as they occur in the markup. Each span represents a plain bit, styled by
        the current style stack.
    """

    def _add_prefix(key: str) -> str:
        """Adds `prefix` to the given key."""

        if key.startswith("@"):
            return "@" + prefix + key[1:]

        return prefix + key

    ctx = ctx or GLOBAL_CONTEXT

    style_stack = cast("dict[str, str | bool]", BASE_STYLE_STACK.copy())
    macros: list[Callable[[str], str]] = []

    get_macro = ctx["macros"].get
    get_alias = ctx["aliases"].get

    text = text.replace("][", " ")

    def _apply_tag(tag: str) -> None:
        """Parses and applies the given tag to the style stack.

        Args:
            tag: The markup tag to apply.
        """

        is_setter = not tag.startswith("/")
        tag = tag.lstrip("/")

        if tag == "" and not is_setter:
            style_stack.update(**BASE_STYLE_STACK)  # type: ignore

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
            macro = get_macro(_add_prefix(tag), None)

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
        found_alias = get_alias(_add_prefix(tag))

        if found_alias is None:
            raise ValueError(f"Unknown tag {tag!r}.")

        for part in found_alias.split():
            _apply_tag(part)

    for mtch in RE_MARKUP.finditer(text):
        tags, plain = mtch.groups()

        if tags is None:
            if plain is None:
                continue

            tags = ""

        plain = plain or ""

        for tag in tags.split():
            if tag == "/":
                yield FULL_RESET

            _apply_tag(tag)

        # TODO: Yield macros to consumer to allow smartly caching things.
        for macro in macros:
            plain = macro(plain)

        should_delete_foreground = _apply_auto_foreground(style_stack)

        yield Span(plain, **style_stack)

        if should_delete_foreground:
            del style_stack["foreground"]


def parse_spans(spans: Iterable[Span]) -> str:  # pylint: disable=too-many-branches
    """Parses spans into an optimized ANSI string.

    Args:
        spans: Any iterable of spans.

    Returns:
        The ANSI styled text the input spans represent. Optimizations are done
        in many places to reduce the output's length and noise.
    """

    style_stack: StyleStack = cast(StyleStack, BASE_STYLE_STACK.copy())

    buff = ""
    hyperlink = ""

    span: Span | None = None

    for span in spans:
        if span is FULL_RESET:
            buff += "\x1b[0m"
            hyperlink = style_stack["hyperlink"]

            style_stack.update(**BASE_STYLE_STACK)  # type: ignore
            style_stack["hyperlink"] = hyperlink

            continue

        stack = BASE_STYLE_STACK.copy()
        unset = []

        for key, value in span.attrs.items():
            if key not in style_stack:
                continue

            if key == "hyperlink":
                stack[key] = value

            if style_stack[key] != value:  # type: ignore
                if value:
                    stack[key] = value

                else:
                    unset.append(key)

        if unset:
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

        buff += str(span.mutate(reset_after=False, **stack))
        buff = buff.removesuffix("\x1b]8;;\x1b\\")

        style_stack.update(**stack)  # type: ignore

    if span is not None:
        if any(span.attrs[key] for key in style_stack if key != "hyperlink"):
            buff += "\x1b[0m"

        if span.hyperlink != "":
            buff += "\x1b]8;;\x1b\\"

    return buff


def markup(text: str, ctx: ContextMapping | None = None, prefix: str = "") -> str:
    """Parses the given markup as a string.

    Under the hood, this joins the `Span` object generated by `markup_spans`.

    Args:
        text: Some markup string.
        ctx: A context mapping to get aliases and macros from. Defaults to the
            global context.
        prefix: The prefix to apply when looking up aliases and macros. Use this to
            compartmentalize markup aliases to each user library.

    Returns:
        The parsed string that is represented by the given markup.
    """

    ctx = ctx or GLOBAL_CONTEXT

    hashable_key = _get_hashable_key(text, ctx, prefix)

    if hashable_key in _markup_cache:
        return _markup_cache[hashable_key]

    buff = parse_spans(markup_spans(text, ctx, prefix))

    _markup_cache[hashable_key] = buff

    return buff
