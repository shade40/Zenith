![zenith](https://singlecolorimage.com/get/4A7A9F/1600x200)

## Zenith

A markup language with a built-in color palette generator, made for the terminal.

```
pip install sh40-zenith
```

![rule](https://singlecolorimage.com/get/4A7A9F/1600x3)

### Purpose

`Zenith` is a fast markup language meant to be readable and maximally accessible. Its
syntax is inspired by [BBCode](https://en.wikipedia.org/wiki/BBCode), but it's meant to
be readable enough that anyone can work with it with no background knowledge.

![rule](https://singlecolorimage.com/get/4A7A9F/1600x3)

### Feature highlights

#### Extensive color & styling support for the terminal

ZML (the Zenith Markup Language) has support for 16, 256 and true color palettes, and
supports both RGB triplets and HEX codes for the latter. A color can set the background
if prefixed by `@`.

`Zenith` is implemented using [Slate](https://github.com/shade40/slate)'s terminal APIs,
and as a result any color set in ZML will be backwards compatible for even the oldest
(xterm-based) terminals!

If you only set a background but no foreground, ZML will choose either black or white
depending on which will be more readable, in accordance to the W3C color contrast guidelines. 

```python3
from zenith import zprint

zprint("[bold 141]Purple & bold,[/] Reset, [@#212121 grey]code,[/bg] and now only grey.")
```

#### Hyperlink support

ZML has a simple syntax to define web-like hyperlinks, which are supported by your terminal!
Simply use the tilde symbol followed by a URI:

```python3
from zenith import zprint

zprint("This looks & functions like a terminal hyperlink: [blue underline ~https://google.com]Google[/]")
```

#### Customizable macros & aliases

We also support macros, which are python functions you can call to transform your
unstyled markup content while it's being parsed. Here is a simple localization system,
implemented using just one macro:

```python
from zenith import zml_macro, zprint

LANG = "en"
LOCALIZATION = {
    "welcome": {
        "en": "Welcome to the project",
        "hu": "Üdv a projektben",
    }
}

@zml_macro
def loc(key: str) -> str:
  """Returns a localized string for the given key."""

  return LOCALIZATION[key][LANG]

zprint("This is localized: [!loc]welcome")
```

If you find yourself often reusing the same set of styles (even including macros), you can
simply alias them:

```python
from zenith import, zml_alias, zprint

zml_alias(title="!upper !gradient(72) bold")

zprint("[title]This is a cool title.[/title]")
```

#### Color palettes

`Zenith` supercharges `Slate`'s 4-color palette generation by adding shades and
aliasing them for use in ZML.

```python
from slate import Color
from zenith import Palette, zprint

palette = Palette(Color.from_hex("#4A7A9F"))
palette.alias()

zprint(palette.render())
```

<p align=center>
    <img src="https://github.com/shade40/Zenith/blob/main/assets/palette.png?raw=true" alt="Palette example" width=300>
</p>

![rule](https://singlecolorimage.com/get/4A7A9F/1600x3)

### Documentation

Once the library gets to a settled state (near 1.0), documentation will be hosted both online and as a celx
application. Until then peep the `experiments` folder, or check out some of the references by using
`python3 -m pydoc <name>`.

![rule](https://singlecolorimage.com/get/4A7A9F/1600x3)

### See also

This library is mostly supposed to _power_ some higher level tools, so using it raw might
not be ideal. Thankfully, we have two projects that can help with that:

- [Slate](https://github.com/shade40/slate): The terminal management library at the core of many of `Zenith`'s
    features.
- [Celadon](https://github.com/shade40/celadon): A TUI library that makes extensive use of ZML for widget
    configuration, and uses the palette generator for quick and great looking UIs.
- [celx](https://github.com/shade40/celx): A hypermedia-driven TUI framework built on top of `Celadon`.
