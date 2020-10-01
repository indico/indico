# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()

print_badge_template = _signals.signal('print-badge-template', """
Called when printing a badge template.
The registration form is passed in the `regform` kwarg. The list of registration
objects are passed in the `registrations` kwarg and it may be modified.
""")
