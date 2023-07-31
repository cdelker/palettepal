''' Color Palettes in HSL and RYB space '''

import colorsys
from collections import namedtuple

from textual.color import Color as tColor


HSL = namedtuple('HSL', 'h s l')
RGB = namedtuple('RGB', 'r g b')


def rgb_to_hsl(r: int, g: int, b: int) -> HSL:
    ''' Convert RGB color tuple to HSL.

        Args:
            r: red (0-255)
            g: green (0-255)
            b: blue (0-255)

        Returns:
            HSL(0-360, 0-100, 0-100)
    '''
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    return HSL(int(h*360+.5), int(s*100+.5), int(l*100+.5))


def hsl_to_rgb(h: int, s: int, l: int) -> RGB:
    ''' Convert HSL color tuple to RGB.

        Args:
            h: hue (0-360)
            s: saturation (0-100)
            l: lightness (0-100)

        Returns:
            r, g, b (0-255)
    '''
    # Note backwards order of colorsys's HLS
    rgbnorm = RGB(*colorsys.hls_to_rgb(h/360, l/100, s/100))
    return RGB(int(rgbnorm.r*255+.5), int(rgbnorm.g*255+.5), int(rgbnorm.b*255+.5))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    ''' Convert RGB color tuple to HSL.

        Args:
            r: red (0-255)
            g: green (0-255)
            b: blue (0-255)

        Returns:
            hex: string starting with #
    '''
    return f'#{r:02x}{g:02x}{b:02x}'


def hex_to_rgb(color: str) -> RGB:
    ''' Convert hex color string to RGB tuple

        Args:
            color: hex color starting with #

        Returns:
            r, g, b: (0-255)
    '''
    color = color.lstrip('#')
    return RGB(int(color[0:2], 16),
               int(color[2:4], 16),
               int(color[4:6], 16))


# Interpolation coefficients for RGB <-> RYB space
# See https://math.stackexchange.com/questions/305395/ryb-and-rgb-color-space-conversion/2776901
# and https://github.com/iskolbin/lryb/blob/master/ryb.lua

GOSSET_RYB_TO_RGB = [
    # Gossett & Chen, "Paint Inspired Color Compositing".
    # Doesn't allow for perfect blacks
    (1.0, 1.0, 1.0),
    (1.0, 0.0, 0.0),
    (1.0, 1.0, 0.0),
    (0.163, 0.373, 0.6),
    (0.5, 0.0, 0.5),
    (0.0, 0.66, 0.2),
    (1.0, 0.5, 0.0),
    (0.2, 0.094, 0.0)]

IRISSON_RYB_TO_RGB = [
    # Irisson Modified to allow perfect blacks
    (1.0, 1.0, 1.0),     #000
    (0.163, 0.373, 0.6), #001
    (1.0, 1.0, 0.0),     #010
    (0.0, 0.66, 0.2),    #011
    (1.0, 0.0, 0.0),     #100
    (0.5, 0.5, 0.9),     #101
    (1.0, 0.5, 0.0),     #110
    (0.0, 0.0, 0.0),     #111
]

RGB_TO_RYB = [
    # Interpolate the other direction
    # Note not all RGB values are representable in RYB space,
    # so conversion is not bi-directional
    (1.0, 1.0, 1.0),     #000
    (0.0, 0.0, 1.0),     #001
    (0.0, 1.0, 0.483),   #010
    (0.0, 0.053, 0.21),  #011
    (1.0, 0.0, 0.0),     #100
    (0.309, 0.0, 0.469), #101
    (0.0, 1.0, 0.0),     #110
    (0.0, 0.0, 0.0),     #111
]

def convert(r: float, y: float, b: float, table=IRISSON_RYB_TO_RGB) -> tuple[float, float, float]:
    ''' Convert RYB using the conversion table

        Args:
            r: red (0-1)
            g: green or yellow (0-1)
            b: blue (0-1)
            table: Conversion table

        Returns:
            r: red (0-1)
            g: green or yellow (0-1)
            b: blue (0-1)
    '''
    f000, f001, f010, f011, f100, f101, f110, f111 = table
    ri, yi, bi = 1-r, 1-y, 1-b
    c000, c001, c010, c011 = ri*yi*bi, ri*yi*b, ri*y*bi, ri*y*b
    c100, c101, c110, c111 = r*yi*bi, r*yi*b, r*y*bi, r*y*b
    return (c000*f000[0] + c001*f001[0] + c010*f010[0] + c011*f011[0] + c100*f100[0] + c101*f101[0] + c110*f110[0] + c111*f111[0],
		    c000*f000[1] + c001*f001[1] + c010*f010[1] + c011*f011[1] + c100*f100[1] + c101*f101[1] + c110*f110[1] + c111*f111[1],
		    c000*f000[2] + c001*f001[2] + c010*f010[2] + c011*f011[2] + c100*f100[2] + c101*f101[2] + c110*f110[2] + c111*f111[2])

def ryb_to_rgb(ryb: RGB) -> RGB:
    ''' Convert RYB to RGB (0-255) '''
    r, y, b = ryb[0]/255, ryb[1]/255, ryb[2]/255
    rgb = convert(r, y, b, table=IRISSON_RYB_TO_RGB)
    return RGB(int(rgb[0]*255+.5), int(rgb[1]*255+.5), int(rgb[2]*255+.5))

def rgb_to_ryb(rgb: RGB) -> RGB:
    ''' Convert RGB to RYB (0-255) '''
    r, g, b = rgb[0]/255, rgb[1]/255, rgb[2]/255
    ryb = convert(r, g, b, table=RGB_TO_RYB)
    return RGB(int(ryb[0]*255+.5), int(ryb[1]*255+.5), int(ryb[2]*255+.5))



class Color:
    ''' Color in RYB space

        Args:
            h: hue (0-360)
            s: saturation (0-100)
            l: lightness (0-100)
            ryb: Use red-yellow-blue color space
    '''
    def __init__(self, h: float, s: float, l: float, ryb: bool=False):
        self._hsl = HSL(h, s, l)
        self._ryb = ryb

    @property
    def hsl(self):
        ''' Hue, Saturation, Lightness value '''
        return self._hsl

    @property
    def rgbnorm(self) -> RGB:
        ''' Normalized RGB (0-1) '''
        rgb = self.rgb
        return RGB(rgb.r/255, rgb.g/255, rgb.b/255)

    @property
    def rgb(self) -> RGB:
        ''' RGB (0-255) '''
        rgb = hsl_to_rgb(*self._hsl)
        if self._ryb:
            return RGB(*ryb_to_rgb(rgb))
        return RGB(*rgb)

    @property
    def ryb(self) -> RGB:
        ''' Red-Yellow-Blue (0-255) '''
        rgb = hsl_to_rgb(*self._hsl)
        if not self._ryb:
            return RGB(*rgb_to_ryb(rgb))
        return RGB(*rgb)

    @property
    def hslnorm(self) -> HSL:
        ''' Normalized HSL (0-1) '''
        return HSL(self._hsl.h/360,
                   self._hsl.s/100,
                   self._hsl.l/100)

    @property
    def hsl_rgbspace(self) -> HSL:
        ''' HSL in RGB space '''
        return HSL(*rgb_to_hsl(*self.rgb))

    @property
    def hex(self) -> str:
        ''' Hexadecimal color '''
        return rgb_to_hex(*self.rgb)

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int, ryb=False) -> 'Color':
        ''' Create Color from RGB (0-255) values '''
        if ryb:
            r, g, b = rgb_to_ryb(RGB(r, g, b))
        hsl = rgb_to_hsl(r, g, b)
        return cls(*hsl, ryb=ryb)

    @classmethod
    def from_hex(cls, color: str) -> 'Color':
        ''' Create color from Hex representation '''
        rgb = hex_to_rgb(color)
        return cls.from_rgb(*rgb)

    @classmethod
    def from_name(cls, color: str) -> 'Color':
        ''' Create color from CSS name '''
        tcolor = tColor.parse(color)
        return cls.from_rgb(*tcolor.rgb)

    @property
    def textual(self) -> tColor:
        ''' Textual Color instance for setting to a Widget style '''
        return tColor(*self.rgb)

    def rotate(self, theta: float):
        ''' Rotate the hue around the color wheel

            Args:
                theta: angle of rotation, in degrees (0-360)
        '''
        h = (self._hsl.h + theta) % 360
        return Color(h, self._hsl.s, self._hsl.l, ryb=self._ryb)

    def lighten(self, add: float=0, mult: float=1) -> 'Color':
        ''' Get a lightened version of the color. New lightness
            is mult * (lightness + add).
        '''
        h, s, l = self.hsl
        l = mult * (l + add)
        l = min(max(l, 0), 100)
        return Color(h, s, l, ryb=self._ryb)

    def saturate(self, add: float = 0, mult: float = 1) -> 'Color':
        ''' Get a saturated version of the color. New saturation
            is mult * (saturation + add)
        '''
        h, s, l = self.hsl
        s = mult * (s + add)
        s = min(max(s, 0), 100)
        return Color(h, s, l, ryb=self._ryb)

    def complement(self) -> tuple['Color']:
        ''' Get complementary color (180 degrees aroud the color wheel) '''
        return (self.rotate(180),)

    def triad(self) -> tuple['Color', 'Color']:
        ''' Get triadic colors (+/- 120 degrees aroud the color wheel) '''
        return self.rotate(120), self.rotate(-120)

    def analagous(self) -> tuple['Color', 'Color']:
        ''' Get analagous colors (+/- 30 degrees aroud the color wheel) '''
        return self.rotate(30), self.rotate(-30)

    def compound(self) ->  tuple['Color', 'Color']:
        ''' Get compound colors (+/- 150 degrees aroud the color wheel) '''
        return self.rotate(150), self.rotate(-150)

    def square(self) ->  tuple['Color', 'Color', 'Color']:
        ''' Get square colors (90 degree increments aroud the color wheel) '''
        return self.rotate(90), self.rotate(180), self.rotate(270)

    def rectangle(self) ->  tuple['Color', 'Color', 'Color']:
        ''' Get rectangular colors (150, 180, 330 degrees aroud the color wheel) '''
        return self.rotate(150), self.rotate(180), self.rotate(330)

    def shades(self) -> tuple['Color', 'Color', 'Color', 'Color']:
        ''' Get lighter and darker shades of the color '''
        return (self.lighten(mult=.5),
                self.lighten(-20),
                self.lighten(20),
                self.lighten(mult=1.5))
