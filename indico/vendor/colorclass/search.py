# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# The code is taken from the colorclass library, release 2.2.0,
# which is licensed under the MIT license and is originally
# available on the following URL:
# https://github.com/Robpol86/colorclass
# Credits of the original code go to Robpol86 (https://github.com/Robpol86)
# and other colorclass contributors.
"""Determine color of characters that may or may not be adjacent to ANSI escape sequences."""

from .parse import RE_SPLIT


def build_color_index(ansi_string):
    """Build an index between visible characters and a string with invisible color codes.

    :param str ansi_string: String with color codes (ANSI escape sequences).

    :return: Position of visible characters in color string (indexes match non-color string).
    :rtype: tuple
    """
    mapping = list()
    color_offset = 0
    for item in (i for i in RE_SPLIT.split(ansi_string) if i):
        if RE_SPLIT.match(item):
            color_offset += len(item)
        else:
            for _ in range(len(item)):
                mapping.append(color_offset)
                color_offset += 1
    return tuple(mapping)


def find_char_color(ansi_string, pos):
    """Determine what color a character is in the string.

    :param str ansi_string: String with color codes (ANSI escape sequences).
    :param int pos: Position of the character in the ansi_string.

    :return: Character along with all surrounding color codes.
    :rtype: str
    """
    result = list()
    position = 0  # Set to None when character is found.
    for item in (i for i in RE_SPLIT.split(ansi_string) if i):
        if RE_SPLIT.match(item):
            result.append(item)
            if position is not None:
                position += len(item)
        elif position is not None:
            for char in item:
                if position == pos:
                    result.append(char)
                    position = None
                    break
                position += 1
    return ''.join(result)
