# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

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

updated = _signals.signal('created', """
Called when a category is modified. The `sender` is the updated category.
""")

deleted = _signals.signal('deleted', """
Called when a category is deleted. The `sender` is the category.
""")
