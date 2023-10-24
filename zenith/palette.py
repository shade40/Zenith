"""The Palette class and its built-in strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Tuple

from slate.color import Color, color

from .markup import MarkupContext, zml_alias, GLOBAL_CONTEXT

__all__ = [
    "triadic",
    "analogous",
    "tetradic",
    "PalettingFunction",
    "Palette",
]

PalettingFunction = Callable[[Color], Tuple[Color, Color, Color, Color]]


def triadic(base: Color) -> tuple[Color, Color, Color, Color]:
    r"""Returns a complementary triangle including base and the base's complement.

    On a colorwheel:

           . 0 .
         .  /|\  .
        .  / | \  .
        . /  |  \ .
         2---+---1
           . 3 .

    """

    return (*base.triadic_group, base.complement)


def analogous(base: Color) -> tuple[Color, Color, Color, Color]:
    """Returns three colors next to eachother, including base.

    On a colorwheel:

           . 0 1
         .       2
        .         .
         .       .
           . 3 .

    """

    return (*base.analogous_group, base.complement)


def tetradic(base: Color) -> tuple[Color, Color, Color, Color]:
    """Returns a complementary square including base.

    On a colorwheel:

           . 0 .
         .       .
        3         1
         .       .
           . 2 .

    """

    return base.tetradic_group


DEFAULT_PANEL = Color.black().blend_complement(0.2)
PANEL_BLEND_ALPHA = 0.05

DEFAULT_TEXT = Color((245, 245, 245))
DEFAULT_SUCCESS = Color.from_hex("67eb7f")
DEFAULT_ERROR = Color.from_hex("eb7067")
DEFAULT_WARNING = Color.from_hex("ebe267")

SEMANTIC_BLEND_ALPHA = 0.3


class Palette:
    def __init__(
        self,
        primary: Color | str | int,
        *,
        namespace: str = "",
        strategy: PalettingFunction = triadic,
        shade_count: int = 3,
        shade_step: float = 0.1,
        text: Color = DEFAULT_TEXT,
        secondary: Color | None = None,
        tertiary: Color | None = None,
        quaternary: Color | None = None,
        success: Color | None = None,
        warning: Color | None = None,
        error: Color | None = None,
        panel1: Color | None = None,
        panel2: Color | None = None,
        panel3: Color | None = None,
        panel4: Color | None = None,
        panel_base: Color = DEFAULT_PANEL,
        success_base: Color = DEFAULT_SUCCESS,
        warning_base: Color = DEFAULT_WARNING,
        error_base: Color = DEFAULT_ERROR,
    ) -> None:
        self._ctx = None
        self._mapping = {}

        self._shade_count = shade_count
        self._shade_step = shade_step
        self._namespace = namespace

        if not isinstance(primary, Color):
            primary = color(str(primary))

        _, g_secondary, g_tertiary, g_quaternary = strategy(primary)

        text = text

        secondary = secondary or g_secondary
        tertiary = tertiary or g_tertiary
        quaternary = quaternary or g_quaternary

        success = success or success_base.blend(primary, SEMANTIC_BLEND_ALPHA)
        warning = warning or warning_base.blend(primary, SEMANTIC_BLEND_ALPHA)
        error = error or error_base.blend(primary, SEMANTIC_BLEND_ALPHA)

        panel1 = panel1 or panel_base.blend(primary, alpha=PANEL_BLEND_ALPHA)
        panel2 = panel2 or panel_base.blend(secondary, alpha=PANEL_BLEND_ALPHA)
        panel3 = panel3 or panel_base.blend(tertiary, alpha=PANEL_BLEND_ALPHA)
        panel4 = panel4 or panel_base.blend(quaternary, alpha=PANEL_BLEND_ALPHA)

        self._keys = {
            "text": text,
            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
            "quaternary": quaternary,
            "success": success,
            "error": error,
            "warning": warning,
            "panel1": panel1,
            "panel2": panel2,
            "panel3": panel3,
            "panel4": panel4,
        }

        self.update(**self._keys)

    def __getattr__(self, attr: str) -> Color:
        if attr not in self._mapping:
            return AttributeError

        return Color.from_hex(self._mapping[attr])

    def update(self, **mapping: Color) -> None:
        shade_count = self._shade_count
        shade_step = self._shade_step
        namespace = self._namespace

        for name, col in mapping.items():
            for i in range(-shade_count, shade_count + 1):
                if i == 0:
                    key = name
                    colorhex = col.hex

                elif i < 0:
                    key = f"{name}{i}"
                    colorhex = col.darken(-i, step_size=shade_step).hex

                else:
                    key = f"{name}+{i}"
                    colorhex = col.lighten(i, step_size=shade_step).hex

                self._mapping[f"{namespace}{key}"] = colorhex
                self._mapping[f"@{namespace}{key}"] = f"@{colorhex}"

    def alias(
        self, ctx: MarkupContext | None = None, ignore_already_aliased: bool = False
    ) -> None:
        """Sets up aliases for the given context.

        It also stores the context as the 'current' context, so it can unalias it later.

        Args:
            ignore_already_aliased: By default, an error is raised if there is already a
                'current' aliased context for this palette. If set, this error is not
                raised.
        """
        if not ignore_already_aliased and self._ctx is not None:
            raise ValueError(
                "either call unalias before trying to re-alias,"
                + " or set `ignore_already_aliased`"
            )

        self._ctx = ctx or GLOBAL_CONTEXT
        zml_alias(**self._mapping, ctx=ctx)

    def unalias(self) -> None:
        """Deletes aliases from the current context.

        It will silently exit if the palette hasn't yet been aliased.
        """

        if self._ctx is None:
            return

        aliases = self._ctx["aliases"]

        for key in self._mapping.keys():
            del aliases[key]
            del aliases[f"/{key}"]

        self._ctx = None

    def render(self) -> str:
        """Returns markup that shows off the palette.

        Note that this is done according to the current `color_mapping`.
        """

        min_width = max(len(key) for key in self._mapping) + 2
        offset_len = len(str(self._shade_count)) + 1
        lines = []
        line = ""

        for key, color in self._mapping.items():
            if not key.startswith("@"):
                continue

            sign, offset = key[-offset_len:]

            if not (sign in ("-", "+") and offset.isdigit()):
                line += f"[{color}]{key:^{min_width}}[/]"

            if key[-offset_len:] == str(-self._shade_count):
                lines.append(line)
                line = ""

            line += f"[{color}]{' ' * 3}[/]"

        return "\n".join(lines)
