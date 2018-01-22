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

from __future__ import unicode_literals

from blinker import Namespace


_signals = Namespace()

registration_personal_data_modified = _signals.signal('registration-personal-data-modified', """
Called when the registration personal data is modified. The `sender` is the
`Registration` object; the change is passed in the `change` kwarg.
""")

registration_state_updated = _signals.signal('registration-state-updated', """
Called when the state of registration changes. The `sender` is the
`Registration` object; the previous state is passed in the `previous_state`
kwarg.
""")

registration_deleted = _signals.signal('registration-deleted', """
Called when a registration is removed. The `sender` is the `Registration` object.
""")

registration_form_created = _signals.signal('registration-form-created', """
Called when a new registration form is created. The `sender` is the
`RegistrationForm` object.
""")

generate_ticket_qr_code = _signals.signal('generate-ticket-qr-code', """
Called when generating the QR code for a ticket. The data included in the QR code is passed
in the `ticket_data` kwarg and may be modified.
""")

registration_form_deleted = _signals.signal('registration-form-deleted', """
Called when a registration form is removed. The `sender` is the
`RegistrationForm` object.
""")

is_ticketing_handled = _signals.signal('is-ticketing-handled', """
Called when resolving whether Indico should send tickets with e-mails
or it will be handled by other module. The `sender` is the
`RegistrationForm` object.

If this signal returns ``True``, no ticket will be emailed on registration.
""")

is_ticket_blocked = _signals.signal('is-ticket-blocked', """
Called when resolving whether Indico should let a registrant download
their ticket.  The `sender` is the registrant's `Registration` object.

If this signal returns ``True``, the user will not be able to download
their ticket.  Any badge containing a ticket-specific placeholder such as
the ticket qr code is considered a ticket, and the restriction applies to
both users trying to get their own ticket and managers trying to get a
ticket for a registrant.
""")
