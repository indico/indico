# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
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
The `template` is the sender. The `item` and it's `styles`
are passed in the kwarg.
The signal returns a dictionary which is used to update the item `style`.
''')

draw_item_on_badge = _signals.signal('draw-item-on-badge', '''
Called when drawing an item on a badge for a given registration.
The `registration` object is the sender. The `items`, `self.height`,
`self.width`, `item_data`, `person` and `template_data` are passed in the kwargs.
`item_data` is a dictionary containing `item`, `text`, `pos_x` and `pos_y`.
`template_data` is a namedtuple containing the complete template structure.
The signal returns a dictionary of updates for the contents of `item_data`.
''')
