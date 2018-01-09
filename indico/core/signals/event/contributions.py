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

from indico.core.signals.event import _signals


contribution_created = _signals.signal('contribution-created', """
Called when a new contribution is created. The `sender` is the new contribution.
""")

contribution_deleted = _signals.signal('contribution-deleted', """
Called when a contribution is deleted. The *sender* is the contribution.
""")

contribution_updated = _signals.signal('contribution-updated', """
Called when a contribution is modified. The *sender* is the contribution.
A dict containing ``old, new`` tuples for all changed values is passed
in the ``changes`` kwarg.
""")


subcontribution_created = _signals.signal('subcontribution-created', """
Called when a new subcontribution is created. The `sender` is the new subcontribution.
""")

subcontribution_deleted = _signals.signal('subcontribution-deleted', """
Called when a subcontribution is deleted. The *sender* is the subcontribution.
""")

subcontribution_updated = _signals.signal('subcontribution-updated', """
Called when a subcontribution is modified. The *sender* is the subcontribution.
""")
