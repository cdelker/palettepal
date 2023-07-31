''' PalettePal color palette app '''

import random
from contextlib import suppress

import pyperclip  # type: ignore
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.color import ColorParseError, COLOR_NAME_TO_RGB
from textual.message import Message
from textual.containers import Horizontal
from textual.widgets import (Footer,
                             Header,
                             Input,
                             Select,
                             Switch,
                             Static)

from . import palette
from .slider import Slider, ColorFade


COLOR_RGB_TO_NAME = {value: key for key, value in COLOR_NAME_TO_RGB.items()}


class ColorPicker(Static):
    ''' Color Picker widget for selecting an HSL or RGB value '''
    DEFAULT_CSS = '''
        ColorPicker {
            width: 100%;
        }
    '''
    def __init__(self, *args, ryb: bool = False, **kwargs):
        ''' Color Picker Widget
        
            Args:
                ryb: Use Red-Yellow-Blue colorspace for HSL colors
        '''
        super().__init__(*args, **kwargs)
        self._ryb = ryb
        self._mode = 'hsl'

    class ColorChanged(Message, bubble=True):
        ''' Message sent when color value was changed '''
        def __init__(self, picker: 'ColorPicker'):
            super().__init__()
            self.picker = picker
            self.color = self.picker.color

        @property
        def control(self) -> 'ColorPicker':
            return self.picker

    def compose(self) -> ComposeResult:
        h, s, l = 250, 100, 50
        yield Slider(label='H', maximum=360, value=h, wrap=True,
                    colorfade=ColorFade(palette.Color(0, s, l, ryb=self.ryb), 'hue'),
                    id='value1')
        yield Slider(label='S', maximum=100, value=s,
                     colorfade=ColorFade(palette.Color(h, 100, l, ryb=self.ryb), 'saturation'),
                     id='value2')
        yield Slider(label='L', maximum=100, value=l,
                     colorfade=ColorFade(palette.Color(h, s, 50, ryb=self.ryb), 'lightness'),
                     id='value3')

    @property
    def color(self):
        ''' Get the selected color '''
        v1 = self.query_one('#value1', Slider).value
        v2 = self.query_one('#value2', Slider).value
        v3 = self.query_one('#value3', Slider).value
        if self._mode == 'rgb':
            return palette.Color.from_rgb(v1, v2, v3)
        return palette.Color(v1, v2, v3, ryb=self.ryb)

    @color.setter
    def color(self, color: palette.Color):
        ''' Set the selected color '''
        if self._mode == 'rgb':
            rgb = color.rgb
            self.query_one('#value1', Slider).value = int(rgb.r)
            self.query_one('#value2', Slider).value = int(rgb.g)
            self.query_one('#value3', Slider).value = int(rgb.b)
        else:  # 'hsl'
            hsl = color.hsl
            self.query_one('#value1', Slider).value = int(hsl.h)
            self.query_one('#value2', Slider).value = int(hsl.s)
            self.query_one('#value3', Slider).value = int(hsl.l)
        self.updatecolor(Slider.ValueChanged(self.query_one('#value1', Slider)))

    @property
    def ryb(self) -> bool:
        ''' Get RYB colorspace mode '''
        return self._ryb

    @ryb.setter
    def ryb(self, value: bool) -> None:
        ''' Set RYB colorspace mode '''
        self._ryb = value
        for slider in self.query(Slider):
            slider.ryb = value
        self.post_message(ColorPicker.ColorChanged(self))

    @on(Slider.ValueChanged)
    def updatecolor(self, message: Slider.ValueChanged):
        ''' Update the color value when a slider was updated. '''
        v1slider = self.query_one('#value1', Slider)
        v2slider = self.query_one('#value2', Slider)
        v3slider = self.query_one('#value3', Slider)
        v1 = v1slider.value
        v2 = v2slider.value
        v3 = v3slider.value
        if message.slider.id == 'value1':
            v1 = message.value
        elif message.slider.id == 'value2':
            v2 = message.value
        elif message.slider.id == 'value3':
            v3 = message.value

        if self._mode == 'rgb':
            v1slider.gradient(palette.Color.from_rgb(0, v2, v3), 'red')
            v2slider.gradient(palette.Color.from_rgb(v1, 0, v3), 'green')
            v3slider.gradient(palette.Color.from_rgb(v1, v2, 0), 'blue')
        else:
            v1slider.gradient(palette.Color(0, v2, v3, ryb=self.ryb), 'hue')
            v2slider.gradient(palette.Color(v1, 100, v3, ryb=self.ryb), 'saturation')
            v3slider.gradient(palette.Color(v1, v2, 50, ryb=self.ryb), 'lightness')
        self.post_message(ColorPicker.ColorChanged(self))

    def changemode(self, mode: str) -> None:
        ''' Change from HSL to RGB selection mode '''
        assert mode in ['rgb', 'hsl']
        self._mode = mode

        v1slider = self.query_one('#value1', Slider)
        v2slider = self.query_one('#value2', Slider)
        v3slider = self.query_one('#value3', Slider)
        if self._mode == 'rgb':
            v1slider._label = 'R'
            v2slider._label = 'G'
            v3slider._label = 'B'
            v1slider._maximum = 255
            v2slider._maximum = 255
            v3slider._maximum = 255
            v1slider.value = self.color.rgb.r
            v2slider.value = self.color.rgb.g
            v3slider.value = self.color.rgb.b
            v1slider.gradient(self.color, parameter='red')
            v2slider.gradient(self.color, parameter='green')
            v3slider.gradient(self.color, parameter='blue')
        else:
            v1slider._label = 'H'
            v2slider._label = 'S'
            v3slider._label = 'L'
            v1slider._maximum = 360
            v2slider._maximum = 100
            v3slider._maximum = 100
            v1slider.value = self.color.hsl.h
            v2slider.value = self.color.hsl.s
            v3slider.value = self.color.hsl.l
            v1slider.gradient(self.color, parameter='hue')
            v2slider.gradient(self.color, parameter='saturation')
            v3slider.gradient(self.color, parameter='lightness')


class ColorSwatch(Static):
    ''' Color Swatch widget. May be selected, displaying an arrow
        above the swatch.
    '''
    DEFAULT_CSS = '''
        ColorSwatch {
            height: 20;
        }
        #indicator {
            height: 1;
            padding: 0;
            content-align: center middle;
        }
        #swatch {
            height: 18;
            content-align: center bottom;
        }
    '''
    def __init__(self, *args, color: palette.Color, label='', **kwargs) -> None:
        ''' Color Swatch widget

            Args:
                color: Initial color to display
                label: Text to show in the widget
        '''
        super().__init__(*args, **kwargs)
        self._color = color
        self._label = label
        self.selected = False

    def compose(self) -> ComposeResult:
        yield Static(id='indicator')
        yield Static(id='swatch')

    @property
    def color(self) -> palette.Color:
        ''' Color being displayed '''
        return self._color

    @color.setter
    def color(self, color: palette.Color) -> None:
        ''' Set the display color '''
        self._color = color
        self.query_one('#swatch', Static).styles.background = color.textual

    def label(self, enable: bool = True) -> None:
        ''' Enable or disable the label '''
        if enable:
            self.query_one('#swatch', Static).update(self._label)
        else:
            self.query_one('#swatch', Static).update('')

    def select(self, show: bool = True) -> None:
        ''' Show this swatch as selected, with an arrow indicator above '''
        if show:
            self.query_one('#indicator', Static).update('▼')
            self.selected = True
        else:
            self.query_one('#indicator', Static).update('')
            self.selected = False


class ColorNumbers(Static):
    ''' Widget for displaying color values and controls '''
    DEFAULT_CSS = '''
        ColorNumbers {
            layout: grid;
            grid-size: 2;
            grid-columns: 5 1fr;
            border: $primary;
            height: 23;
            width: 34;
            margin: 0;
        }
        .label {
            height: 3;
            margin-left: 1;
            content-align: center middle;
            width: auto;
        }
        .input {
            width: 29;
        }
    '''
    class ColorChanged(Message, bubble=True):
        ''' Message sent when color input was changed '''
        def __init__(self, picker: 'ColorNumbers'):
            super().__init__()
            self.picker = picker
            self.color: palette.Color = self.picker.color

        @property
        def control(self) -> 'ColorNumbers':
            return self.picker

    class PaletteChanged(Message, bubble=True):
        ''' Message sent when the palette type was changed '''
        def __init__(self, picker: 'ColorNumbers'):
            super().__init__()
            self.picker = picker
            self.name = self.picker.query_one('#palette', Select).value

    def compose(self) -> ComposeResult:
        yield Static('Mode', classes='label')
        yield Select((('HSL', 'hsl'),
                      ('HSL (RYB Space)', 'ryb'),
                      ('RGB', 'rgb')),
                      value='hsl', prompt='Entry Mode', id='mode')
        yield Static('RGB', classes='label')
        yield Input(id='rgb', classes='input')
        yield Static('HSL', classes='label')
        yield Input(id='hsl', classes='input')
        yield Static('Hex', classes='label')
        yield Input(id='hex', classes='input')
        yield Static('Name', classes='label')
        yield Input(id='name', classes='input')
        yield Static('Norm', classes='label')
        yield Switch(id='normalize')
        yield Static()
        yield Select((('Custom', 'custom'),
                      ('Complementary', 'Complementary'),
                      ('Analagous', 'Analagous'),
                      ('Triadic', 'Triadic'),
                      ('Compound', 'Compound'),
                      ('Square', 'Square'),
                      ('Rectangle', 'Rectangle'),
                      ('Monochrome', 'Monochrome')),
                      prompt='Palette', classes='input', id='palette')

    def on_mount(self):
        ''' Widget was mounted, set an initial color '''
        self._color = palette.Color(255, 100, 50)

    @property
    def normalized(self) -> bool:
        ''' Normalized mode is toggled '''
        return self.query_one('#normalize', Switch).value

    @property
    def color(self) -> palette.Color:
        ''' Get the current color '''
        return self._color

    @color.setter
    def color(self, color: palette.Color) -> None:
        ''' Set the current color, updating all the Inputs '''
        self._color = color
        self._sethsl(color)
        self._setrgb(color)
        self._sethex(color)
        self._setname(color)

    def disable_entry(self, disable: bool) -> None:
        ''' Disable entry of color values '''
        self.query_one('#hsl', Input).disabled = disable
        self.query_one('#rgb', Input).disabled = disable
        self.query_one('#hex', Input).disabled = disable
        self.query_one('#name', Input).disabled = disable

    def _sethsl(self, color: palette.Color) -> None:
        ''' Set the HSL display value to the given color '''
        # Note: always showing HSL in RGB space
        hslinput = self.query_one('#hsl', Input)
        hsl = color.hsl_rgbspace  # Normalized
        with hslinput.prevent(Input.Changed):
            if self.normalized:
                hslinput.value = f'({hsl.h/360:.3f}, {hsl.s/100:.3f}, {hsl.l/100:.3f})'
            else:
                hslinput.value = f'({hsl.h}, {hsl.s}, {hsl.l})'

    def _setrgb(self, color: palette.Color) -> None:
        ''' Set the RGB display value to the given color '''
        rgb = self.query_one('#rgb', Input)
        with rgb.prevent(Input.Changed):
            if self.normalized:
                r, g, b = color.rgbnorm
                rgb.value = f'({r:.3f}, {g:.3f}, {b:.3f})'
            else:
                rgb.value = f'({color.rgb.r}, {color.rgb.g}, {color.rgb.b})'

    def _sethex(self, color: palette.Color) -> None:
        ''' Set the Hex display value to the given color '''
        hx = self.query_one('#hex', Input)
        with hx.prevent(Input.Changed):
            hx.value = color.hex

    def _setname(self, color: palette.Color) -> None:
        ''' Set the color name display value to the given color if it has a CSS name '''
        name = self.query_one('#name', Input)
        with name.prevent(Input.Changed):
            name.value = COLOR_RGB_TO_NAME.get(color.rgb, 'N/A')

    @on(Input.Submitted, '#rgb')
    def setrgb(self, event: Input.Changed) -> None:
        ''' RGB Input was changed '''
        with suppress(ValueError):  # not 3 values or not integers
            rgb = event.value.strip('() ').split(',')
            r, g, b = float(rgb[0]), float(rgb[1]), float(rgb[2])
            if self.normalized:
                r, g, b = r*255, g*255, b*255

            color = palette.Color.from_rgb(int(r), int(g), int(b))
            self._color = color
            self._sethsl(color)
            self._sethex(color)
            self._setname(color)
            self.post_message(ColorNumbers.ColorChanged(self))

    @on(Input.Submitted, '#hsl')
    def sethsl(self, event: Input.Changed) -> None:
        ''' HSL Input was changed '''
        with suppress(ValueError):  # not 3 values or not integers
            hsl = event.value.strip('() ').split(',')
            if self.normalized:
                h = int(hsl[0]) * 360
                s = int(hsl[0]) * 100
                l = int(hsl[0]) * 100
            else:
                h, s, l = int(h), int(s), int(l)
            color = palette.Color(h, s, l)
            self._color = color
            self._setrgb(color)
            self._sethex(color)
            self._setname(color)
            self.post_message(ColorNumbers.ColorChanged(self))

    @on(Input.Submitted, '#hex')
    def sethex(self, event: Input.Changed) -> None:
        ''' Hex input was changed '''
        with suppress(ColorParseError):
            color = palette.Color.from_hex(event.value)
            self._color = color
            self._sethsl(color)
            self._setrgb(color)
            self._setname(color)
            self.post_message(ColorNumbers.ColorChanged(self))

    @on(Input.Submitted, '#name')
    def setname(self, event: Input.Changed) -> None:
        ''' Name input was changed '''
        with suppress(ColorParseError):
            color = palette.Color.from_name(event.value)
            self._color = color
            self._sethsl(color)
            self._setrgb(color)
            self._sethex(color)
            self.post_message(ColorNumbers.ColorChanged(self))

    @on(Switch.Changed, '#normalize')
    def normchange(self, event: Switch.Changed) -> None:
        ''' Normalize switch was flipped '''
        self._sethsl(self._color)
        self._setrgb(self._color)
        self._sethex(self._color)
        self._setname(self._color)

    @on(Select.Changed, '#palette')
    def palettechange(self, event: Select.Changed) -> None:
        ''' Palette selection was changed '''
        self.post_message(ColorNumbers.PaletteChanged(self))


class PalettePal(App):
    ''' Main Application '''
    CSS = '''
    ColorPicker {
        border: $primary;
    }
    ColorSwatch {
        width: 1fr;
    }
    '''
    BINDINGS = [Binding('d', 'toggle_dark', 'Toggle dark mode'),
                Binding('!', 'randomize', 'Randomize'),
                Binding('f1', 'select_swatch(1)', 'Color 1', show=False),
                Binding('f2', 'select_swatch(2)', 'Color 2', show=False),
                Binding('f3', 'select_swatch(3)', 'Color 3', show=False),
                Binding('f4', 'select_swatch(4)', 'Color 4', show=False),
                Binding('f5', 'select_swatch(5)', 'Color 5', show=False),
                Binding('h', 'copy("hsl")', 'Copy HSL', show=True),
                Binding('r', 'copy("rgb")', 'Copy RGB', show=True),
                Binding('x', 'copy("hex")', 'Copy Hex', show=True)]

    def compose(self) -> ComposeResult:
        yield Header()
        yield ColorPicker()
        with Horizontal():
            yield ColorNumbers()
            yield ColorSwatch(color=palette.Color(0,100,50), label='<F1>', id='color1')
            yield ColorSwatch(color=palette.Color(90,100,50), label='<F2>', id='color2')
            yield ColorSwatch(color=palette.Color(180,100,50), label='<F3>', id='color3')
            yield ColorSwatch(color=palette.Color(270,100,50), label='<F4>', id='color4')
            yield ColorSwatch(color=palette.Color(300,100,50), label='<F5>', id='color5')
        yield Footer()

    def on_mount(self) -> None:
        ''' Set the initial color on mount '''
        self.set_color(palette.Color(250, 100, 50))

    @on(ColorPicker.ColorChanged)
    def colorchanged(self, message):
        ''' ColorPicker value was changed, update swatches '''
        self.set_color(message.color)
        self.query_one(ColorNumbers).color = self.selected_swatch().color

    @on(ColorNumbers.ColorChanged)
    def colornum_changed(self, message):
        ''' ColorNumber Input box was changed, update swatches '''
        picker = self.query_one(ColorPicker)
        with picker.prevent(ColorPicker.ColorChanged):
            picker.color = message.color
        self.set_color(message.color)

    @on(ColorNumbers.PaletteChanged)
    def set_palette(self, message):
        ''' Palette type was changed '''
        palette_name = message.name
        if palette_name is None:
            for i in range(5):
                self.query_one(f'#color{i+1}', ColorSwatch).select(False)
            self.set_color(self.query_one('#color1', ColorSwatch).color)

        elif palette_name == 'custom':
            self.query_one('#color1', ColorSwatch).select(True)
            for i in range(5):
                self.query_one(f'#color{i+1}', ColorSwatch).display = True
        else:
            self.fill_palette(message.name)
            self.query_one('#color1', ColorSwatch).select(True)

        self.query_one('#color1', ColorSwatch).label(palette_name is not None)
        self.query_one('#color2', ColorSwatch).label(palette_name is not None)
        self.query_one('#color3', ColorSwatch).label(palette_name is not None)
        self.query_one('#color4', ColorSwatch).label(palette_name is not None)
        self.query_one('#color5', ColorSwatch).label(palette_name is not None)

    def selected_swatch(self) -> ColorSwatch:
        ''' Get the currently selected swatch '''
        for i in range(5):
            c = self.query_one(f'#color{i+1}', ColorSwatch)
            if c.selected:
                return c
        return self.query_one('#color1', ColorSwatch)

    def fill_palette(self, name: str = 'custom') -> None:
        ''' Fill the palette colors based on color swatch #1 '''
        basecolor = self.query_one('#color1', ColorSwatch).color
        colors = {'Monochrome': basecolor.shades,
                  'Triadic': basecolor.triad,
                  'Complementary': basecolor.complement,
                  'Square': basecolor.square,
                  'Rectangle': basecolor.rectangle,
                  'Compound': basecolor.compound,
                  'Analagous': basecolor.analagous}.get(name, basecolor.triad)()

        swatches = [self.query_one(f'#color{i+2}', ColorSwatch) for i in range(4)]
        for swatch, color in zip(swatches, colors):
            swatch.color = color

        for i in range(5):
            self.query_one(f'#color{i+1}', ColorSwatch).display = i < len(colors)+1

    def set_color(self, color: palette.Color):
        ''' Set the color. Either swatch #1, or the selected swatch
            if in custom palette mode.
        '''
        palette_name = self.query_one('#palette', Select).value
        if not palette_name:
            # No palette, single color
            self.query_one('#color1', ColorSwatch).color = color
            self.query_one('#color2', ColorSwatch).color = color
            self.query_one('#color3', ColorSwatch).color = color
            self.query_one('#color4', ColorSwatch).color = color
            self.query_one('#color5', ColorSwatch).color = color

        elif palette_name == 'custom':
            # Custom palette. Change one color at a time
            for i in range(5):
                c = self.query_one(f'#color{i+1}', ColorSwatch)
                if c.selected:
                    c.color = color
        else:
            self.query_one('#color1', ColorSwatch).color = color   # only change color1 directly
            self.fill_palette(palette_name)

    def action_randomize(self) -> None:
        ''' Pick a random color '''
        h = random.randint(0, 360)
        s = random.randint(20, 100)  # Limit to avoid too light/dark
        l = random.randint(20, 80)
        picker = self.query_one(ColorPicker)
        color = palette.Color(h, s, l, ryb=picker.ryb)
        picker.color = color

    def action_select_swatch(self, num: int) -> None:
        ''' A swatch was selected '''
        for i in range(5):
            self.query_one(f'#color{i+1}', ColorSwatch).select(False)
        swatch = self.query_one(f'#color{num}', ColorSwatch)
        swatch.select(True)
        if self.query_one('#palette', Select).value == 'custom':
            self.query_one(ColorPicker).color = swatch.color
        self.query_one(ColorNumbers).color = swatch.color

    @on(Select.Changed, '#mode')
    def entry_mode(self, message: Select.Changed) -> None:
        ''' Entry mode (HSL, HSL/RYB, or RGB) was changed '''
        picker = self.query_one(ColorPicker)
        if message.value == 'ryb':
            picker.ryb = True
            picker.changemode('hsl')
            self.query_one(ColorNumbers).disable_entry(True)

        elif message.value == 'hsl':
            picker.ryb = False
            picker.changemode('hsl')
            self.query_one(ColorNumbers).disable_entry(False)
        else:
            picker.changemode('rgb')
            self.query_one(ColorNumbers).disable_entry(False)

    def action_copy(self, fmt: str = 'rgb'):
        ''' Copy the color string to the system clipboard '''
        color = self.selected_swatch().color
        if fmt == 'hsl':
            if self.query_one('#normalize', Switch).value:
                hsl = color.hslnorm
            else:
                hsl = color.hsl
            value = f'{hsl.h}, {hsl.s}, {hsl.l}'
            self.notify(f"HSL: {value}", title="Copied")
        elif fmt == 'hex':
            value = color.hex
            self.notify(f"Hex: {value}", title="Copied")
        else:
            if self.query_one('#normalize', Switch).value:
                rgb = color.rgbnorm
            else:
                rgb = color.rgb
            value = f'{rgb.r}, {rgb.g}, {rgb.b}'
            self.notify(f"RGB: {value}", title="Copied")
        pyperclip.copy(value)


def main():
    ''' Start the App '''
    app = PalettePal()
    app.run()


if __name__ == "__main__":
    main()
