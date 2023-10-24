from functools import lru_cache
from time import strftime
from typing import Callable, Literal

from slate.color import Color

from .markup import parse_color, zml_macro, zml_pre_process


def transform(text: str, transformer: Callable[[int, str], str]) -> str:
    """Applies the given transformation for all non-style chars, returns the result."""

    i = 0
    output = ""
    in_group = False

    for char in text:
        if char in "[]":
            output += char
            in_group = char == "["
            continue

        if in_group:
            output += char
            continue

        output += transformer(i, char)
        i += 1

    return output


@zml_macro
def upper(text: str) -> str:
    """Returns `text.upper()`."""

    return transform(text, lambda _, text: text.upper())


@zml_macro
def lower(text: str) -> str:
    """Returns `text.lower()`."""

    return transform(text, lambda _, text: text.lower())


@zml_macro
def title(text: str) -> str:
    """Returns `text.title()`."""

    return transform(text, lambda _, text: text.title())


@zml_macro
def time(template: str, time_format: str = "%s") -> str:
    """Formats the template's `time` key as `time.strftime(time_format)`."""

    return template.format(time=strftime(time_format))


@zml_macro
@lru_cache
def gradient(
    text: str, origin: str, method: Literal["shade", "rainbow"] = "shade"
) -> str:
    """Adds a gradient into the given plain text.

    Args:
        origin: The start of the gradient.
        method: The type of gradient to apply.
    """

    is_background = origin.startswith("@")
    origin = zml_pre_process(f"[{origin}]")[1:-1]
    color = Color.from_ansi(parse_color(origin.lstrip("@"), is_background))

    if method == "shade":
        steps = [
            color.darken(4),
            color.darken(2),
            color,
            color.lighten(2),
            color.lighten(4),
        ]

    elif method == "rainbow":
        steps = [
            color,
            color.hue_shift(1 / 5),
            color.hue_shift(2 / 5),
            color.hue_shift(3 / 5),
            color.hue_shift(4 / 5),
        ]

    else:
        raise ValueError(r"Unknown gradient method {method!r}.")

    blocksize = max(round(len(text) / 5), 1)

    def _transform(i: int, char: str) -> str:
        if len(steps) > 0 and i % blocksize == 0:
            color = steps.pop(0)

            return f"[{'@' * color.is_background}{color.hex}]{char}"

        return char

    return transform(text, _transform) + f"[{'/bg' if is_background else '/fg'}]"


@zml_macro
def alpha(text: str, color: str, opacity: str) -> str:
    """Converts the given color to some opacity."""

    if opacity == "1.0":
        return zml_pre_process(f"[{color}]{text}")

    color = zml_pre_process(f"[{color}]")[1:-1]
    background = color.startswith("@")

    color = ";".join(parse_color(color.lstrip("@"), background).split(";")[2:])
    color += f";{opacity}"

    return f"[{'@' * background}{color}]{text}"
