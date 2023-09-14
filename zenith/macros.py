from time import strftime
from typing import Literal
from functools import lru_cache

from slate.color import Color

from .markup import zml_macro, parse_color


@zml_macro
def upper(text: str) -> str:
    """Returns `text.upper()`."""

    return text.upper()


@zml_macro
def lower(text: str) -> str:
    """Returns `text.lower()`."""

    return text.lower()


@zml_macro
def title(text: str) -> str:
    """Returns `text.title()`."""

    return text.title()


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

    output = ""
    current_block = 0
    blocksize = max(round(len(text) / 5), 1)

    for i, char in enumerate(text):
        if i % blocksize == 0 and current_block < len(steps):
            color = steps[current_block]
            output += f"[{'@' if color.is_background else ' '}{color.hex}]"

            current_block += 1

        output += char

    return output + ("[/bg]" if is_background else "[/fg]")
