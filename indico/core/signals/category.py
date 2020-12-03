# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


moved = _signals.signal('moved', """
Called when a category is moved into another category. The `sender` is
the category and the old parent category is passed in the `old_parent`
kwarg.
""")

created = _signals.signal('created', """
Called when a new category is created. The `sender` is the new category.
""")

updated = _signals.signal('updated', """
Called when a category is modified. The `sender` is the updated category.
""")

deleted = _signals.signal('deleted', """
Called when a category is deleted. The `sender` is the category.
""")
