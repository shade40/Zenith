import colorsys

from slate import terminal, ColorSpace, getch
from zenith import zml, zml_get_spans, zml_pre_process


def _normalize(_rgb: tuple[float, float, float]) -> str:
    normalized = tuple(str(int(_col * 255)) for _col in _rgb)

    return normalized[0], normalized[1], normalized[2]


def _get_colorbox(width: int) -> str:
    _buff = ""

    for y_pos in range(0, 5):
        for x_pos in range(width):
            # Mmmm, spiky code
            _hue = x_pos / width
            _lightness = 0.1 + ((y_pos / 5) * 0.7)
            _rgb1 = colorsys.hls_to_rgb(_hue, _lightness, 1.0)
            _rgb2 = colorsys.hls_to_rgb(_hue, _lightness + 0.07, 1.0)

            _bg_color = ";".join(_normalize(_rgb1))
            _color = ";".join(_normalize(_rgb2))
            _buff += f"[{_bg_color} @{_color}]▀"

        _buff += "\n"

    return _buff


def _draw_colorbox(markup: str) -> None:
    for line in markup.splitlines():
        for span in zml_get_spans(line):
            terminal.write(span)

        terminal.cursor = 0, terminal.cursor[1] + 1

    terminal.draw()
    terminal.cursor = 0, terminal.cursor[1] + 1

    zml_get_spans.cache_clear()


markup = _get_colorbox(50)

from zenith.markup import parse_color, Color

for color_space in ColorSpace:
    terminal.color_space = color_space

    terminal.write(zml(f"ColorSpace: [bold]{color_space.name}"))
    terminal.cursor = 0, terminal.cursor[1] + 1

    _draw_colorbox(markup)

print()
getch()

with open("color_grids.svg", "w") as output:
    output.write(terminal.export_svg())
