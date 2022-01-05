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
"""Color class used by library users."""

from .core import ColorStr


class Color(ColorStr):
    """str subclass with ANSI terminal text color support.

    Example syntax: Color('{red}Sample Text{/red}')

    Example without parsing logic: Color('{red}Sample Text{/red}', keep_tags=True)
    """
