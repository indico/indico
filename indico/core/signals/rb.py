# This file is part of Indico.
# Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from blinker import Namespace


_signals = Namespace()


booking_created = _signals.signal('booking-created', """
Executed after a booking has been successfully created. The *sender*
is the new `Reservation` object.
""")

booking_state_changed = _signals.signal('booking-state-changed', """
Executed after a booking has been cancelled/rejected/accepted. The *sender*
is the `Reservation` object.
""")

booking_deleted = _signals.signal('booking-deleted', """
Executed after a booking has been deleted. The *sender* is the `Reservation` object.
""")

booking_occurrence_state_changed = _signals.signal('booking-occurrence-state-changed', """
Executed after the state of a booking occurrence changed.
The *sender* is the `ReservationOccurrence` object.
""")
