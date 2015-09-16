# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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
Called when the parent of a category is changed. The `sender` is the category,
the old/new parents are passed using the `old_parent` and `new_parent` kwargs.
""")

created = _signals.signal('created', """
Called when a new category is created. The `sender` is the new category, its
parent category is passed in the `parent` kwarg.
""")

deleted = _signals.signal('deleted', """
Called when a category is deleted. The `sender` is the category.
""")

title_changed = _signals.signal('title-changed', """
Called when the title of a category is changed. The `sender` is the category,
the old/new titles are passed in the `old` and `new` kwargs.
""")

data_changed = _signals.signal('data-changed', """
Called when some data of the category changed. The `sender` is the category.
""")

protection_changed = _signals.signal('protection-changed', """
Called when the protection mode of the category changed. The `sender` is the category,
`old`/`new` contain the corresponding values.
""")

domain_access_granted = _signals.signal('domain-access-granted', """
Called when an IP restriction is added to a category. The `sender` is the category class,
the `domain` is that domain that has been added.
""")

domain_access_revoked = _signals.signal('domain-access-revoked', """
Called when an IP restriction is removed from a category. The `sender` is the category class,
the `domain` is that domain that has been removed.
""")
