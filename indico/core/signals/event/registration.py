# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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


registration_state_updated = _signals.signal('registration-state-updated', """
Called when the state of registration changes.  The `sender` is the
registration; the previous state is passed in the `previous_state`
kwarg.
""")

registration_deleted = _signals.signal('registration-deleted', """
Called when a registration is removed.  The `sender` is the registration.
""")

registration_form_created = _signals.signal('registration-form-created', """
Called when a new registration form is created.  The `sender` is the
`RegistrationForm` object.
""")
