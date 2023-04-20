from zenith.color import Color
from zenith.markup import markup
from zenith.palette import Palette

p = Palette.from_hex("#7c93d0")
p.alias()

STEP_SIZE = 0.1
STEP_COUNT = 5

lines = []
for key, color in p.color_mapping.items():
    print(key, color.hex, color.luminance)
    for i in range(-STEP_COUNT, STEP_COUNT + 1):
        li = i + STEP_COUNT

        try:
            line = lines[li]
        except IndexError:
            lines.append([])
            line = lines[-1]

        if i < 0:
            line.append(f"[@{color.darken(-i, STEP_SIZE).hex}]      ")
        elif i == 0:
            line.append(f"[@{color.hex}]      ")
        else:
            line.append(f"[@{color.lighten(i, STEP_SIZE).hex}]      ")

for line in lines:
    print(markup("[/]".join(line)))

print(markup("[surface1+3]Test text[@surface1-2] on background"))
