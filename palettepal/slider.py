''' Textual Slider widget with color gradient '''
from collections import namedtuple

from textual.app import RenderResult
from textual.message import Message
from textual.binding import Binding
from textual import events
from textual.widgets import Static
from textual.color import Color as tColor
from rich.text import Text
from rich.style import Style

from . import palette


ColorFade = namedtuple('ColorFade', 'color parameter')


class Slider(Static, can_focus=True):
    ''' Slider widget with a gradient bar and value display '''
    COMPONENT_CLASSES = {
    "slider--pointer",
    "slider--label",
    "slider--value",
    "slider--valuefocus",
    }

    DEFAULT_CSS = '''
        Slider>.slider--pointer {
            color: $text;
        }
        Slider>.slider--label {
            color: $text;
        }
        Slider>.slider--value {
            color: $text;
            text-style: bold;
        }
        Slider>.slider--valuefocus {
            color: $text;
            text-style: bold reverse;
        }
    '''
    BINDINGS = [Binding("left", "increment(-1)", "Decrement", show=False),
                Binding("down", "increment(-1)", "Decrement", show=False),
                Binding("right", "increment(1)", "Increment", show=False),
                Binding("up", "increment(1)", "Increment", show=False),
                Binding("shift+right", "increment(10)", "Large Increment", show=False),
                Binding("shift+up", "increment(10)", "Large Increment", show=False),
                Binding("shift+left", "increment(-10)", "Large Decrement", show=False),
                Binding("shift+down", "increment(-10)", "Large Decrement", show=False)]

    class ValueChanged(Message, bubble=True):
        ''' Message sent when slider value changes '''
        def __init__(self, slider: 'Slider'):
            super().__init__()
            self.slider = slider
            self.value = self.slider.value

        @property
        def control(self) -> 'Slider':
            return self.slider

    def __init__(self,
                 *args,
                 label: str = 'H',
                 value: int = 100,
                 maximum: int = 100,
                 colorfade: ColorFade = None,
                 wrap: bool = True,
                 ryb: bool = False,
                 **kwargs):
        ''' Slider widget

            Args:
                label: label for left of slider bar
                value: initial value
                maximum: maximum value
                colorfade: Color and color parameter
                wrap: Wrap input from max to min
                ryb: use RYB colorspace
            '''
        super().__init__(*args, **kwargs)
        self._label = label
        self._value = value
        self._maximum = maximum
        self._wrap = wrap
        self._colors: list[tColor] = []
        self._ryb = ryb
        if colorfade is None:
            self.colorfade = ColorFade(palette.Color(0, 100, 50, self.ryb), 'hue')
        else:
            self.colorfade = colorfade

    @property
    def barwidth(self) -> int:
        ''' Get width of the bar portion of slider '''
        return self.size.width - len(self._label) - (len(str(self._maximum))) - 4

    @property
    def value(self) -> int:
        ''' Selected value '''
        return self._value

    @value.setter
    def value(self, value: int) -> None:
        ''' Set selected value '''
        self._value = value
        self.refresh()

    @property
    def ryb(self) -> bool:
        ''' Get RYB mode '''
        return self._ryb

    @ryb.setter
    def ryb(self, value: bool) -> None:
        ''' Set RYB mode '''
        self._ryb = value
        self._makegradient()
        self.refresh()

    def on_mount(self):
        ''' Initialize the gradient '''
        self._makegradient()

    def on_resize(self):
        ''' Resize the widget, remake the gradient for new width '''
        self._makegradient()

    def render(self) -> RenderResult:
        ''' Draw the Slider '''
        parts = []

        # Draw pointer
        pointerstyle = self.get_component_rich_style('slider--pointer')
        width = self.barwidth
        pad = ' ' * (len(self._label)+2)
        pos = int(self._value / self._maximum * width) - 1
        pos = min(pos, width-1)
        parts.append((pad + ' ' * pos + '▼' + '\n', pointerstyle))

        # label
        labelstyle = self.get_component_rich_style('slider--label')
        parts.append((f' {self._label} ', labelstyle))

        # bar
        if len(self._colors) != width:
            self._makegradient()
        for color in self._colors:
            cstyle = Style.from_color(color.rich_color)
            parts.append(('█', cstyle))

        # value
        parts.append((' ', self.get_component_rich_style('slider--value')))
        if self.has_focus:
            valuestyle = self.get_component_rich_style('slider--valuefocus')
        else:
            valuestyle = self.get_component_rich_style('slider--value')
        parts.append((str(self._value), valuestyle))
        return Text.assemble(*parts)

    def gradient(self, color: palette.Color, parameter: str='hue') -> None:
        ''' Set the color gradient

            Args:
                color: Base color
                parameter: parameter to sweep along the bar. May be
                    'hue', 'saturation', 'lightness', 'red', 'green, 'blue'.
        '''
        self.colorfade = ColorFade(color, parameter)
        self._makegradient()
        self.refresh()

    def _makegradient(self):
        ''' Create the gradient colors '''
        self._colors = []
        width = self.barwidth
        if self.colorfade.parameter in ['hue', 'saturation', 'lightness']:
            hsl = self.colorfade.color.hsl
            hue = hsl.h #* 360
            sat = hsl.s #* 100
            light = hsl.l #* 100
            for i in range(width):
                if self.colorfade.parameter == 'hue':
                    hue = i/width * 360
                elif self.colorfade.parameter == 'saturation':
                    sat = i/width * 100
                elif self.colorfade.parameter == 'lightness':
                    light = i/width * 100
                self._colors.append(palette.Color(hue, sat, light, ryb=self.ryb).textual)

        elif self.colorfade.parameter in ['red', 'green', 'blue']:
            red, green, blue = self.colorfade.color.rgb
            for i in range(width):
                if self.colorfade.parameter == 'red':
                    red = int(i/width*255 + .5)
                elif self.colorfade.parameter == 'green':
                    green = int(i/width*255 + .5)
                elif self.colorfade.parameter == 'blue':
                    blue = int(i/width*255 + .5)
                self._colors.append(palette.Color.from_rgb(red, green, blue).textual)

        else:
            raise NotImplementedError

    def action_increment(self, value=1):
        ''' Increment/decrement the value '''
        self._value += value
        if self._wrap:
            self._value = self._value % (self._maximum+1)
        self._value = min(self._value, self._maximum)
        self._value = max(0, self._value)
        self.refresh()
        self.post_message(Slider.ValueChanged(self))

    def on_key(self, event: events.Key) -> None:
        ''' Key was pressed. Update the input value. '''
        if event.key.isdigit():
            newvalue = str(self._value) + event.key
            newvalue = newvalue[-3:]  # Keep 3 digits
            self._value = int(newvalue)
            self.refresh()
            self.post_message(Slider.ValueChanged(self))
