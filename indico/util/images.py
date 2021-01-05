# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

"""
Image processing functions
"""


def square(image):
    """Return a squared image.

    :param image: a `PIL.Image` object
    """
    width, height = image.size
    if width == height:
        return image
    side = min(width, height)
    overflow = max(width, height) - side
    margin = overflow / 2
    if width > height:
        box = (margin, 0, margin + side, side)
    else:
        box = (0, margin, side, margin + side)
    return image.crop(box)
