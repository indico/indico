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


event_sidemenu = _signals.signal('event-sidemenu', """
Expected to return ``EventMenuEntry`` objects to be added to the event side menu.
A single entry can be returned directly, multiple entries must be yielded.
""")

event_deleted = _signals.signal('event-deleted', """
Called when an event is deleted. The *sender* is the event object.
""")

event_data_changed = _signals.signal('event-data-changed', """
Called when the basic data of an event is changed. The `sender` is the event,
and the following kwargs are available:

* `attr` - the changed attribute (`title`, `description`, `dates`, `start_date`, `end_date` or `location`)
* `old` - the old value
* `new` - the new value

If the `dates` changed, both `old` and `new` are ``(start_date, end_date)`` tuples.
If the `location` changed, both `old` and `new` are dicts containing `location`, `address` and `room`.

`attr` may be ``None`` in cases where it's not known which data has been changed.
In that case, both `old` and `new` are ``None``, too.

If your plugin reacts to date changes, always make sure to handle all three types.
Depending on the code performing the change, sometimes separate `start_date` and
`end_date` changes are triggered while in other cases a single `dates` change is
triggered.
""")

event_moved = _signals.signal('event-moved', """
Called when an event is moved to a different category. The `sender` is the event,
the old/new categories are passed using the `old_parent` and `new_parent` kwargs.
""")

event_created = _signals.signal('event-created', """
Called when a new event is created. The `sender` is the new event, its
parent category is passed in the `parent` kwarg.
""")

event_protection_changed = _signals.signal('event-protection-changed', """
Called when the protection mode of the event changed. The `sender` is the event,
`old`/`new` contain the corresponding values.
""")

session_slot_deleted = _signals.signal('session-slot-deleted', """
Called when a session slot is deleted. The *sender* is the session slot.
""")

material_downloaded = _signals.signal('material-downloaded', """
Notifies a file being downloaded. The *sender* is the event and the downloaded
file is passed in the *resource* kwarg.
""")

timetable_buttons = _signals.signal('timetable-buttons', """
Expected to return a list of tuples ('button_name', 'js_call_name').
Called when building the timetable view.
""")

event_registrant_changed = _signals.signal('event-registrant-changed', """
Called when an event registrant is added or removed. The `sender` is the event,
and the following kwargs are available:

* `user` - the registrant's :class:`Avatar` (or ``None``)
* `registrant` - the :class:`Registrant`
* `action` - the action, i.e. ``'removed'`` or ``'added'``
""")

event_participant_changed = _signals.signal('event-participant-changed', """
Called when an event participant is added or removed. The `sender` is the event,
and the following kwargs are available:

* `user` - the participant's :class:`Avatar` (or ``None``)
* `participant` - the :class:`Participant`
* `old_status` - the previous participation status
* `action` - the action, i.e. ``'removed'`` or ``'added'``

This signal is only triggered if the participation state actually changed, i.e. he's
considered `added` if he was added/approved by a manager or if he accepted an invitation.
The participant is considered `removed` if he's participating (added by a manager or accepted
an invitation) and he's removed from the event or refuses/rejects participation.
""")
