![zenith](https://singlecolorimage.com/get/4A7A9F/1600x200)

## zenith

A markup language and color palette generators targeting the terminal.

```
pip install sh40-zenith
```

![rule](https://singlecolorimage.com/get/4A7A9F/1600x5)

### Purpose

The primary usecase for Zenith is to color and style text in the terminal. We do this through 2 connected systems, our markup language and palette generation.

We use a [BBCode](https://en.wikipedia.org/wiki/BBCode) inspired markup language, where you define tag _groups_, and specific styles within each group. Every tag is independent of others, so you can set and unset single styles easily. We also support custom tag aliases, macro functions and more!

```
Welcome to [bold #4A7A9F]Zenith[/fg]!
```

Our palette generator applies color theory to generate a nice, aesthetically pleasing and UX-optimized color palette from any primary color. You can optionally get a palette aliased, so you can use shades derived from its colors:

```python
from zenith import Palette, markup

palette = Palette.from_hex("#4A7A9F")
palette.alias()
print(markup(palette.render()))

print(markup("[primary-2]Primary foreground color, darkened twice"))
```

![result](https://github.com/shade40/zenith/blob/main/assets/readme_purpose_1.png?raw=true)

![rule](https://singlecolorimage.com/get/4A7A9F/1600x5)

### Examples
