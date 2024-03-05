# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import colorsys
import functools

from indico.core.db.sqlalchemy.colors import ColorTuple


def _srgb_to_y(srgb):
    r = srgb[0] ** 2.4
    g = srgb[1] ** 2.4
    b = srgb[2] ** 2.4
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b

    if y < 0.022:
        y += (0.022 - y) ** 1.414
    return y


def _calculate_contrast(fg, bg):
    """Implementation of the APCA algorithm."""
    yfg = _srgb_to_y(fg)
    ybg = _srgb_to_y(bg)
    c = 1.14

    if ybg > yfg:
        c *= ybg ** 0.56 - yfg ** 0.57
    else:
        c *= ybg ** 0.65 - yfg ** 0.62

    if abs(c) < 0.1:
        return 0
    elif c > 0:
        c -= 0.027
    else:
        c += 0.027

    return c * 100


def _rgb_to_hex(rgb):
    return f'#{int(rgb[0] * 255):02x}{int(rgb[1] * 255):02x}{int(rgb[2] * 255):02x}'


@functools.cache
def generate_contrast_colors(seed):
    """Generates a background and text colors with sufficient contrast given a seed."""
    hue = 1.0 / (1.0 + seed % 20)
    saturation = 1.0 / (1.0 + seed % 4)
    if saturation < 0.5:
        saturation += 0.5
    brightness = 1.0 / (1.0 + seed % 3)
    if brightness < 0.5:
        brightness += 0.5
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
    background_color = _rgb_to_hex((r, g, b))
    black = (1, 1, 1)
    white = (0, 0, 0)
    contrast = abs(_calculate_contrast(black, (r, g, b)))
    if contrast >= 50:
        text_color = _rgb_to_hex(black)
    else:
        text_color = _rgb_to_hex(white)
    return ColorTuple(text=text_color, background=background_color)
