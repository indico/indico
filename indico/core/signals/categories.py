# This file is part of Indico.
# Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

from indico.core.signals import _signals


category_moved = _signals.signal('category-moved', """
Called when the parent of a category is changed. The `sender` is the category,
the old/new parents are passed using the `old_parent` and `new_parent` kwargs.
""")

category_created = _signals.signal('category-created', """
Called when a new category is created. The `sender` is the new category, its
parent category is passed in the `parent` kwarg.
""")

category_deleted = _signals.signal('category-deleted', """
Called when a category is deleted. The `sender` is the category.
""")

category_title_changed = _signals.signal('category-title-changed', """
Called when the title of a category is changed. The `sender` is the category,
the old/new titles are passed in the `old` and `new` kwargs.
""")

category_data_changed = _signals.signal('category-data-changed', """
Called when some data of the category changed. The `sender` is the category.
""")

category_protection_changed = _signals.signal('category-protection-changed', """
Called when the protection mode of the category changed. The `sender` is the category,
`old`/`new` contain the corresponding values.
""")

category_domain_access_granted = _signals.signal('category-domain-access-granted', """
Called when an IP restriction is added to a category. The `sender` is the category class,
the `domain` is that domain that has been added.
""")

category_domain_access_revoked = _signals.signal('category-domain-access-revoked', """
Called when an IP restriction is removed from a category. The `sender` is the category class,
the `domain` is that domain that has been removed.
""")
