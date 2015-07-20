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

from indico.core.signals.event import _signals


sidemenu = _signals.signal('sidemenu', """
Expected to return ``EventMenuEntry`` objects to be added to the event side menu.
A single entry can be returned directly, multiple entries must be yielded.
""")

deleted = _signals.signal('deleted', """
Called when an event is deleted. The *sender* is the event object.
The `user` kwarg contains the user performing the deletion if available.
""")

data_changed = _signals.signal('data-changed', """
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

moved = _signals.signal('moved', """
Called when an event is moved to a different category. The `sender` is the event,
the old/new categories are passed using the `old_parent` and `new_parent` kwargs.
""")

created = _signals.signal('created', """
Called when a new event is created. The `sender` is the new event, its
parent category is passed in the `parent` kwarg.
""")

protection_changed = _signals.signal('protection-changed', """
Called when the protection mode of the event changed. The `sender` is the event,
`old`/`new` contain the corresponding values.
""")

domain_access_granted = _signals.signal('domain-access-granted', """
Called when an IP restriction is added to an event. The `sender` is the event class,
the `domain` is that domain that has been added.
""")

domain_access_revoked = _signals.signal('domain-access-revoked', """
Called when an IP restriction is removed from an event. The `sender` is the event class,
the `domain` is that domain that has been removed.
""")

session_deleted = _signals.signal('session-deleted', """
Called when a session slot is deleted. The *sender* is the session.
""")

session_slot_deleted = _signals.signal('session-slot-deleted', """
Called when a session slot is deleted. The *sender* is the session slot.
""")

timetable_buttons = _signals.signal('timetable-buttons', """
Expected to return a list of tuples ('button_name', 'js-call-class').
Called when building the timetable view.
""")

registrant_changed = _signals.signal('registrant-changed', """
Called when an event registrant is added or removed. The `sender` is the event,
and the following kwargs are available:

* `user` - the registrant's :class:`Avatar` (or ``None``)
* `registrant` - the :class:`Registrant`
* `action` - the action, i.e. ``'removed'`` or ``'added'``
""")

participant_changed = _signals.signal('participant-changed', """
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

has_read_access = _signals.signal('has-read-access', """
Called when resolving the read access permissions for an event. The `sender` is the event,
and the following parameters are available:

* `user` - the user that is trying to access the event (:class:`.User` or ``None``)

Should return ``True`` or ``False``.
""")

get_log_renderers = _signals.signal('get-log-renderers', """
Expected to return `EventLogRenderer` classes.
""")
