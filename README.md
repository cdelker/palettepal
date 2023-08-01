# Palettepal

Generate color palettes from your terminal.

Install with:

```
pip install palettepal
```

And run from the command line:

```
python -m palettepal
```

Palettepal requires textual and pyperclip.

## Usage

Use the arrow keys to move the color slider position. Hold `shift` while using arrow keys to move it faster.

Color values may be entered directly into the HSL, RGB, Hex, or Name boxes. These entries are disabled in `HSL (RYB Space)` because not all RGB colors are mappable to Red-Yellow-Blue colors.

Change the color palette selection to display complementary colors using a few defined schemes. The function keys change which color values are displayed in the Input boxes, but the sliders only control the first base color of the palette. Using the `custom` palette allows the sliders to change the selected color in the palette.

Press `R`, `H`, or `X` to copy the RGB, HSL, or Hex value to the system clipboard (via pyperclip) for use in other applications.
