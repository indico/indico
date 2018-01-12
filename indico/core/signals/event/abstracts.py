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


abstract_created = _signals.signal('abstract-created', """
Called when a new abstract is created. The `sender` is the new abstract.
""")

abstract_deleted = _signals.signal('abstract-deleted', """
Called when an abstract is deleted. The *sender* is the abstract.
""")

abstract_state_changed = _signals.signal('abstract-state-changed', """
Called when an abstract is withdrawn. The *sender* is the abstract.
""")

abstract_updated = _signals.signal('abstract-updated', """
Called when an abstract is modified. The *sender* is the abstract.
""")
