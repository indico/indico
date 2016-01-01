# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from indico.core.signals.event import _signals


contribution_created = _signals.signal('contribution-created', """
Called when a new contribution is created. The `sender` is the new contribution,
its parent category is passed in the `parent` kwarg.
""")

contribution_deleted = _signals.signal('contribution-deleted', """
Called when a contribution is deleted. The *sender* is the contribution, the parent
event is passed in the `parent` kwarg.
""")

contribution_title_changed = _signals.signal('contribution-title-changed', """
Called when the title of a contribution is changed. The `sender` is the contribution,
the old/new titles are passed in the `old` and `new` kwargs.
""")

contribution_data_changed = _signals.signal('contribution-data-changed', """
Called when some data of the contribution changed. The `sender` is the contribution.
""")

contribution_protection_changed = _signals.signal('contribution-protection-changed', """
Called when the protection mode of the contribution changed. The `sender` is the contribution,
`old`/`new` contain the corresponding values.
""")

subcontribution_created = _signals.signal('subcontribution-created', """
Called when a new subcontribution is created. The `sender` is the new subcontribution,
its parent category is passed in the `parent` kwarg.
""")

subcontribution_deleted = _signals.signal('subcontribution-deleted', """
Called when a subcontribution is deleted. The *sender* is the subcontribution, the parent
contribution is passed in the `parent` kwarg.
""")

subcontribution_title_changed = _signals.signal('subcontribution-title-changed', """
Called when the title of a subcontribution is changed. The `sender` is the subcontribution,
the old/new titles are passed in the `old` and `new` kwargs.
""")

subcontribution_data_changed = _signals.signal('subcontribution-data-changed', """
Called when some data of the subcontribution changed. The `sender` is the subcontribution.
""")
