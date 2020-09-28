# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from blinker import Namespace


_signals = Namespace()

registration_personal_data_modified = _signals.signal('registration-personal-data-modified', """
Called when the registration personal data is modified. The `sender` is the
`Registration` object; the change is passed in the `change` kwarg.
""")

registration_state_updated = _signals.signal('registration-state-updated', """
Called when the state of a registration changes. The `sender` is the
`Registration` object; the previous state is passed in the `previous_state`
kwarg.
""")

registration_checkin_updated = _signals.signal('registration-checkin-updated', """
Called when the checkin state of a registration changes. The `sender` is the
`Registration` object.
""")

registration_created = _signals.signal('registration-created', """
Called when a new registration has been created. The `sender` is the `Registration` object.
The `data` kwarg contains the form data used to populate the registration fields.
The `management` kwarg is set to `True` if the registration was created from the event management area.
""")

registration_updated = _signals.signal('registration-updated', """
Called when a registration has been updated. The `sender` is the `Registration` object.
The `data` kwarg contains the form data used to populate the registration fields.
The `management` kwarg is set to `True` if the registration was updated from the event management area.
""")

registration_deleted = _signals.signal('registration-deleted', """
Called when a registration is removed. The `sender` is the `Registration` object.
""")

registration_form_wtform_created = _signals.signal('registration_form_wtform_created', """
Called when a the wtform is created for rendering/processing a registration form.
The sender is the `RegistrationForm` object. The generated WTForm class is
passed in the `wtform_cls` kwarg and it may be modified. The `registration`
kwarg contains a `Registration` object when called from registration edit
endpoints. The `management` kwarg is set to `True` if the registration form is
rendered/processed from the event management area.
""")

registration_form_created = _signals.signal('registration-form-created', """
Called when a new registration form is created. The `sender` is the
`RegistrationForm` object.
""")

registration_form_edited = _signals.signal('registration-form-edited', """
Called when a registration form is edited. The `sender` is the
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

filter_selectable_badges = _signals.signal('filter-selectable-badges', """
Called when composing lists of badge templates. The `sender` may be either
``BadgeSettingsForm``, ``RHListEventTemplates`` or ``RHListCategoryTemplates``.
The list of badge templates is passed in the `badge_templates` kwarg.
The signal handler is expected to mutate the list.
""")
