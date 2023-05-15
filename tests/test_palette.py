from slate.color import Color
from zenith.markup import zml_context
from zenith.palette import Palette, analogous, tetradic, triadic


def test_palette_triadic():
    pal = Palette.from_hex("#FABCDE", strategy=triadic)

    assert pal.primary == Color.from_hex("#FABCDE")
    assert pal.secondary == pal.primary.hue_shift(1 / 3)
    assert pal.tertiary == pal.primary.hue_shift(2 / 3)
    assert pal.quaternary == pal.primary.complement


def test_palette_analogous():
    pal = Palette.from_hex("#EDCBAF", strategy=analogous)

    assert pal.primary == Color.from_hex("#EDCBAF")
    assert pal.secondary == pal.primary.hue_shift(1 / 12)
    assert pal.tertiary == pal.primary.hue_shift(2 / 12)
    assert pal.quaternary == pal.primary.complement


def test_palette_tetradic():
    pal = Palette.from_hex("#F45A11", strategy=tetradic)

    assert pal.primary == Color.from_hex("#F45A11")
    assert pal.secondary == pal.primary.hue_shift(1 / 4)
    assert pal.tertiary == pal.primary.hue_shift(2 / 4)
    assert pal.quaternary == pal.primary.hue_shift(3 / 4)


def test_palette_alias():
    pal = Palette.from_hex("#42DFBC")
    ctx = zml_context()

    pal.alias(ctx=ctx)

    assert ctx["aliases"]["error-2"] == pal.error.darken(2).hex
    assert ctx["aliases"]["surface3"] == pal.surface3.hex
    assert ctx["aliases"]["success+3"] == pal.success.lighten(3).hex

    assert "success+4" not in ctx["aliases"]
    assert "primary-5" not in ctx["aliases"]
