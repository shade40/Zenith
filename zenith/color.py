from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property

from .color_info import COLOR_TABLE

OFF_WHITE = (245, 245, 245)
OFF_BLACK = (35, 35, 35)


@dataclass(frozen=True)
class Color:
    rgb: tuple[int, int, int]
    is_background: bool = False

    @classmethod
    def from_ansi(cls, ansi: str) -> Color:
        """Creates a color instance from an ANSI sequence's body."""

        parts = ansi.split(";")
        if len(parts) > 3:
            is_background = parts[0].startswith("4")

            return Color((parts[2:]), is_background=is_background)

        ansi = parts[-1]

        # TODO: Handle garbage

        index = int(ansi)
        is_background = False

        # Convert indices to 16-color
        if len(parts) == 1:
            if 30 <= index < 38:
                index -= 30

            elif 40 <= index < 48:
                index -= 40
                is_background = True

            if 90 <= index < 98:
                index -= 82

            elif 100 <= index < 108:
                index -= 92
                is_background = True

        return Color(COLOR_TABLE[index], is_background=is_background)

    @cached_property
    def ansi(self) -> str:
        return f"{38 + 10*self.is_background};2;{';'.join(map(str, self.rgb))}"

    @cached_property
    def luminance(self) -> float:
        """Returns this color's perceived luminance (brightness).

        From https://stackoverflow.com/a/596243
        """

        def _linearize(color: float) -> float:
            """Converts sRGB color to linear value."""

            if color <= 0.04045:
                return color / 12.92

            return ((color + 0.055) / 1.055) ** 2.4

        red, green, blue = float(self.rgb[0]), float(self.rgb[1]), float(self.rgb[2])

        red /= 255
        green /= 255
        blue /= 255

        red = _linearize(red)
        blue = _linearize(blue)
        green = _linearize(green)

        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    @cached_property
    def contrast(self) -> Color:
        """Returns a color (black or white) that complies with the W3C contrast ratio guidelines.

        Note that the returned color will not keep the original's `is_background` property.
        """

        if self.luminance > 0.179:
            return Color(OFF_BLACK, is_background=self.is_background)

        return Color(OFF_WHITE, is_background=self.is_background)

    def as_background(self, setting: bool = True) -> Color:
        """Returns this color, with the given background setting."""

        return Color(self.rgb, is_background=setting)
