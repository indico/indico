# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.


from blinker import Namespace


_signals = Namespace()


items = _signals.signal('items', """
Expected to return one or more `SideMenuItem` to be added to the side
menu.  The *sender* is an id string identifying the target menu.
""")

sections = _signals.signal('sections', """
Expected to return one or more `SideMenuSection` objects to be added to
the side menu.  The *sender* is an id string identifying the target menu.
""")
