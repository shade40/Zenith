"""The Palette class and its built-in strategies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Tuple

from slate.color import Color

from .markup import MarkupContext, zml_alias

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


DEFAULT_SURFACE = Color.black().blend_complement(0.2)
SURFACE_BLEND_ALPHA = 0.2

DEFAULT_SUCCESS = Color.from_hex("67eb7f")
DEFAULT_ERROR = Color.from_hex("eb7067")
DEFAULT_WARNING = Color.from_hex("ebe267")
SEMANTIC_BLEND_ALPHA = 0.3


@dataclass
class Palette:  # pylint: disable=too-many-instance-attributes
    """A palette containing 4 'main' colors and surface colors and 3 semantics ones.

    The primary color is the main color of an interface. Secondary, tertiary and
    quaternary colors are calculated based on the given strategy.

    Success, warning & error are colors representing the given semantic meanings; they
    are computed by tinting some defaults with the primary color.

    Additionally, there are surface colors defined for all 4 of the main ones; these are
    created by tinting a default surface color with the primary, secondary, tertiary and
    quaternary color respectively.
    """

    primary: Color
    secondary: Color = field(init=False)
    tertiary: Color = field(init=False)
    quaternary: Color = field(init=False)

    success: Color = field(init=False)
    warning: Color = field(init=False)
    error: Color = field(init=False)

    surface1: Color = field(init=False)
    surface2: Color = field(init=False)
    surface3: Color = field(init=False)
    surface4: Color = field(init=False)

    surface_blend_base: Color = DEFAULT_SURFACE
    success_blend_base: Color = DEFAULT_SUCCESS
    warning_blend_base: Color = DEFAULT_WARNING
    error_blend_base: Color = DEFAULT_ERROR

    strategy: PalettingFunction = triadic

    def __post_init__(self) -> None:
        primary = self.primary

        _, self.secondary, self.tertiary, self.quaternary = self.strategy(primary)

        self.success = self.success_blend_base.blend(primary, SEMANTIC_BLEND_ALPHA)
        self.warning = self.warning_blend_base.blend(primary, SEMANTIC_BLEND_ALPHA)
        self.error = self.error_blend_base.blend(primary, SEMANTIC_BLEND_ALPHA)

        self.surface1 = self.surface_blend_base.blend(
            self.primary,
            alpha=SURFACE_BLEND_ALPHA,
        )
        self.surface2 = self.surface_blend_base.blend(
            self.secondary,
            alpha=SURFACE_BLEND_ALPHA,
        )
        self.surface3 = self.surface_blend_base.blend(
            self.tertiary,
            alpha=SURFACE_BLEND_ALPHA,
        )
        self.surface4 = self.surface_blend_base.blend(
            self.quaternary,
            alpha=SURFACE_BLEND_ALPHA,
        )

        self.color_mapping = {
            "primary": self.primary,
            "secondary": self.secondary,
            "tertiary": self.tertiary,
            "quaternary": self.quaternary,
            "surface1": self.surface1,
            "surface2": self.surface2,
            "surface3": self.surface3,
            "surface4": self.surface4,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
        }

    @classmethod
    def from_hex(cls, primary: str, strategy: PalettingFunction = triadic) -> Palette:
        """Generates a palette from a CSS-style HEX color string."""

        return Palette(Color.from_hex(primary), strategy=strategy)

    @property
    def color_mapping(self) -> dict[str, Color]:
        """Returns a mapping of color names to their values.

        Primarily used for aliasing.
        """

        return self._color_mapping

    @color_mapping.setter
    def color_mapping(self, new: dict[str, Color]) -> None:
        """Sets the color mapping."""

        self._color_mapping = new

    def alias(
        self,
        ctx: MarkupContext | None = None,
        mapping: dict[str, Color] | None = None,
        shade_count: int = 3,
        shade_step: float = 0.1,
    ) -> None:
        """Sets up aliases for this palette's colors.

        Args:
            ctx: The markup context to alias into. Defaults to the global context.
            mapping: The name->color mapping used to set up the aliases. Defaults to
                `self.color_mapping`.
            shade_count: The number of shades that should be included on both the
                positive and negative side. These are aliased as `{color}{+/-step}`,
                like `primary+2` or `surface1-2`.
            shade_step: The step_size passed to `Color.lighten` or `Color.darken`,
                controls the distance between shades.
        """

        mapping = mapping or self.color_mapping

        for name, color in mapping.items():
            for i in range(-shade_count, shade_count + 1):
                if i == 0:
                    key = name
                    colorhex = color.hex

                elif i < 0:
                    key = f"{name}{i}"
                    colorhex = color.darken(-i, step_size=shade_step).hex

                else:
                    key = f"{name}+{i}"
                    colorhex = color.lighten(i, step_size=shade_step).hex

                zml_alias(**{key: colorhex, f"@{key}": f"@{colorhex}"}, ctx=ctx)  # type: ignore

    def render(self) -> str:
        """Returns markup that shows off the palette.

        Note that this is done according to the current `color_mapping`.
        """

        min_width = max(len(key) for key in self.color_mapping) + 2
        lines = []

        for key, color in self.color_mapping.items():
            line = ""

            for shade in range(-3, 4):
                if shade < 0:
                    line += f"[@{color.darken(-shade, 0.1).hex}]{' ' * 3}[/]"

                elif shade == 0:
                    line += f"[@{color.hex}]{key:^{min_width}}[/]"

                else:
                    line += f"[@{color.lighten(shade, 0.1).hex}]{' ' * 3}[/]"

            lines.append(line)

        return "\n".join(lines)
