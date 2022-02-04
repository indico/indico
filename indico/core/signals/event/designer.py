# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()

print_badge_template = _signals.signal('print-badge-template', '''
Called when printing a badge template.
The registration form is passed in the `regform` kwarg. The list of registration
objects are passed in the `registrations` kwarg and it may be modified.
''')

update_badge_style = _signals.signal('update-badge-style', '''
Called when printing a badge.

Each `item` in a badge and it's `styles` are passed in the kwarg.
The return value is dictionary which is used to update the item `style`.
''')

draw_item_on_badge = _signals.signal('draw-item-on-badge', '''
Called when drawing a badge for a given registration on a pdf.

The `updates` is a dictionary containing information required to
draw the items on a pdf at the given position.

The return value is dictionary with the updates.
''')
