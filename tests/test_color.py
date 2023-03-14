from zenith.color import Color
from zenith.color_info import COLOR_TABLE


def test_from_ansi():
    assert Color.from_ansi("31") == Color(COLOR_TABLE[1])
    assert Color.from_ansi("45") == Color(COLOR_TABLE[5], is_background=True)
    assert Color.from_ansi("93") == Color(COLOR_TABLE[11])
    assert Color.from_ansi("105") == Color(COLOR_TABLE[13], is_background=True)


def test_luminance():
    assert Color((38, 45, 125)).luminance == 0.03769509660602206
    assert Color((145, 121, 67)).luminance == 0.20099734269321143


def test_contrast():
    assert Color((255, 255, 255)).contrast == Color((35, 35, 35))
    assert Color((67, 10, 193), is_background=True).contrast == Color(
        (245, 245, 245),
        is_background=True,
    )
