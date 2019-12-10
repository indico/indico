# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db.sqlalchemy.colors import ColorTuple


def get_colors():
    return [
        ColorTuple('#1D041F', '#EEE0EF'),
        ColorTuple('#253F08', '#E3F2D3'),
        ColorTuple('#1F1F02', '#FEFFBF'),
        ColorTuple('#202020', '#DFE555'),
        ColorTuple('#1F1D04', '#FFEC1F'),
        ColorTuple('#0F264F', '#DFEBFF'),
        ColorTuple('#EFF5FF', '#0D316F'),
        ColorTuple('#F1FFEF', '#1A3F14'),
        ColorTuple('#FFFFFF', '#5F171A'),
        ColorTuple('#272F09', '#D9DFC3'),
        ColorTuple('#FFEFFF', '#4F144E'),
        ColorTuple('#FFEDDF', '#6F390D'),
        ColorTuple('#021F03', '#8EC473'),
        ColorTuple('#03070F', '#92B6DB'),
        ColorTuple('#151515', '#DFDFDF'),
        ColorTuple('#1F1100', '#ECC495'),
        ColorTuple('#0F0202', '#B9CBCA'),
        ColorTuple('#0D1E1F', '#C2ECEF'),
        ColorTuple('#000000', '#D0C296'),
        ColorTuple('#202020', '#EFEBC2')
    ]


def get_sui_colors():
    return [
        'red',
        'orange',
        'yellow',
        'olive',
        'green',
        'teal',
        'blue',
        'violet',
        'purple',
        'pink',
        'brown',
        'grey',
        'black'
    ]
