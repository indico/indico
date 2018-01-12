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


timetable_entry_created = _signals.signal('timetable-entry-created', """
Called when a new timetable entry is created. The `sender` is the new entry.
""")

timetable_entry_updated = _signals.signal('timetable-entry-updated', """
Called when a timetable entry is updated. The `sender` is the entry.
A dict containing ``old, new`` tuples for all changed values is passed
in the ``changes`` kwarg.
""")

timetable_entry_deleted = _signals.signal('timetable-entry-deleted', """
Called when a timetable entry is deleted. The `sender` is the entry.
This signal is triggered right before the entry deletion is performed.
""")

times_changed = _signals.signal('times-changed', """
Called when the times of a scheduled object (contribution, break or
session block) change, either by a change in duration or start time.
The `sender` is the type of the object; the timetable entry is passed
as `entry` and the object is passed as `obj`.  Information about the
changes are passed as `changes` which is a dict containing old/new
tuples for `start_dt`, `duration` and `end_dt`.  If an attribute did
not change, it is not included in the dict.
If the time of the event itself changes, `entry` is ``None`` and `obj`
contains the `Event`.
""")
