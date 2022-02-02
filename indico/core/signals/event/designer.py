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

customize_badge_style = _signals.signal('customize-badge-style', '''
Called when printing a badge.
Each `item` in a badge and it's `styles` are passed in the kwarg. The `styles` is a dictionary
which may be modified and is used to update the `item style`.
''')
