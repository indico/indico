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
"""Handles mapping between color names and ANSI codes and determining auto color codes."""

from collections.abc import Mapping


BASE_CODES = {
    '/all': 0, 'b': 1, 'f': 2, 'i': 3, 'u': 4, 'flash': 5, 'outline': 6, 'negative': 7, 'invis': 8, 'strike': 9,
    '/b': 22, '/f': 22, '/i': 23, '/u': 24, '/flash': 25, '/outline': 26, '/negative': 27, '/invis': 28,
    '/strike': 29, '/fg': 39, '/bg': 49,

    'black': 30, 'red': 31, 'green': 32, 'yellow': 33, 'blue': 34, 'magenta': 35, 'cyan': 36, 'white': 37,

    'bgblack': 40, 'bgred': 41, 'bggreen': 42, 'bgyellow': 43, 'bgblue': 44, 'bgmagenta': 45, 'bgcyan': 46,
    'bgwhite': 47,

    'hiblack': 90, 'hired': 91, 'higreen': 92, 'hiyellow': 93, 'hiblue': 94, 'himagenta': 95, 'hicyan': 96,
    'hiwhite': 97, 'grey': 90,  # alias for hiblack

    'hibgblack': 100, 'hibgred': 101, 'hibggreen': 102, 'hibgyellow': 103, 'hibgblue': 104, 'hibgmagenta': 105,
    'hibgcyan': 106, 'hibgwhite': 107, 'bggrey': 100,  # alias for hibgblack

    '/black': 39, '/red': 39, '/green': 39, '/yellow': 39, '/blue': 39, '/magenta': 39, '/cyan': 39, '/white': 39,
    '/hiblack': 39, '/hired': 39, '/higreen': 39, '/hiyellow': 39, '/hiblue': 39, '/himagenta': 39, '/hicyan': 39,
    '/hiwhite': 39, '/grey': 39,

    '/bgblack': 49, '/bgred': 49, '/bggreen': 49, '/bgyellow': 49, '/bgblue': 49, '/bgmagenta': 49, '/bgcyan': 49,
    '/bgwhite': 49, '/hibgblack': 49, '/hibgred': 49, '/hibggreen': 49, '/hibgyellow': 49, '/hibgblue': 49,
    '/hibgmagenta': 49, '/hibgcyan': 49, '/hibgwhite': 49, '/bggrey': 49
}


class ANSICodeMapping(Mapping):
    """Read-only dictionary, resolves closing tags and automatic colors. Iterates only used color tags.
    """

    def __init__(self, value_markup):
        """Constructor.

        :param str value_markup: String with {color} tags.
        """
        self.whitelist = [k for k in BASE_CODES if '{' + k + '}' in value_markup]

    def __getitem__(self, item):
        """Return value for key or None if colors are disabled.

        :param str item: Key.

        :return: Color code integer.
        :rtype: int
        """
        if item not in self.whitelist:
            raise KeyError(item)
        return getattr(self, item, BASE_CODES[item])

    def __iter__(self):
        """Iterate dictionary."""
        return iter(self.whitelist)

    def __len__(self):
        """Dictionary length."""
        return len(self.whitelist)
