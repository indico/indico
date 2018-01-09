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


sidemenu = _signals.signal('sidemenu', """
Expected to return ``MenuEntryData`` objects to be added to the event side menu.
A single entry can be returned directly, multiple entries must be yielded.
""")

deleted = _signals.signal('deleted', """
Called when an event is deleted. The *sender* is the event object.
The `user` kwarg contains the user performing the deletion if available.
""")

updated = _signals.signal('updated', """
Called when basic data of an event is updated. The *sender* is the event.
A dict of changes is passed in the `changes` kwarg, with ``(old, new)``
tuples for each change. Note than the `person_links` change may happen
with `old` and `new` being the same lists for technical reasons. If the
key is present, it should be assumed that something changed (usually
the order or some data on the person link).
""")

cloned = _signals.signal('cloned', """
Called when an event is cloned. The *sender* is the `Event` object of
the old event, the new event is passed in the `new_event` kwarg.
""")

type_changed = _signals.signal('type-changed', """
Called when the type of an event is changed. The `sender` is the event,
the old type is passed in the `old_type` kwarg.
""")

moved = _signals.signal('moved', """
Called when an event is moved to a different category. The `sender` is the event,
the old category is in the `old_parent` kwarg.
""")

created = _signals.signal('created', """
Called when a new event is created. The `sender` is the new Event.
""")

session_updated = _signals.signal('session-updated', """
Called when a session is updated. The *sender* is the session.
""")

session_deleted = _signals.signal('session-deleted', """
Called when a session is deleted. The *sender* is the session.
""")

session_block_deleted = _signals.signal('session-block-deleted', """
Called when a session block is deleted. The *sender* is the session block.
This signal is called before the ``db.session.delete()`` on the block is
executed.
""")

timetable_buttons = _signals.signal('timetable-buttons', """
Expected to return a list of tuples ('button_name', 'js-call-class').
Called when building the timetable view.
""")

get_log_renderers = _signals.signal('get-log-renderers', """
Expected to return `EventLogRenderer` classes.
""")

get_feature_definitions = _signals.signal('get-feature-definitions', """
Expected to return `EventFeature` subclasses.
""")
