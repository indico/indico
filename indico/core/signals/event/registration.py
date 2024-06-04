# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()

registration_personal_data_modified = _signals.signal('registration-personal-data-modified', '''
Called when the registration personal data is modified. The `sender` is the
`Registration` object; the change is passed in the `change` kwarg.
''')

registration_state_updated = _signals.signal('registration-state-updated', '''
Called when the state of a registration changes. The `sender` is the
`Registration` object; the previous state is passed in the `previous_state`
kwarg; the `silent` kwarg can be set to `True` to skip logging.
''')

registration_checkin_updated = _signals.signal('registration-checkin-updated', '''
Called when the checkin state of a registration changes. The `sender` is the
`Registration` object.
''')

registration_created = _signals.signal('registration-created', '''
Called when a new registration has been created. The `sender` is the `Registration` object.
The `data` kwarg contains the form data used to populate the registration fields.
The `management` kwarg is set to `True` if the registration was created from the event management area.
''')

registration_updated = _signals.signal('registration-updated', '''
Called when a registration has been updated. The `sender` is the `Registration` object.
The `data` kwarg contains the form data used to populate the registration fields.
The `management` kwarg is set to `True` if the registration was updated from the event management area.
''')

registration_deleted = _signals.signal('registration-deleted', '''
Called when a registration is removed. The `sender` is the `Registration` object.
The `permanent` kwarg indicates whether the registration is being permanently deleted from the database,
e.g. due to it exceeding its retention period.
''')

registration_form_created = _signals.signal('registration-form-created', '''
Called when a new registration form is created. The `sender` is the
`RegistrationForm` object.
''')

registration_form_edited = _signals.signal('registration-form-edited', '''
Called when a registration form is edited. The `sender` is the
`RegistrationForm` object.
''')

generate_ticket_qr_code = _signals.signal('generate-ticket-qr-code', '''
Called when generating the QR code for a ticket. The data included in the QR code is passed
in the `ticket_data` kwarg and may be modified. The signal may also return a string which
will then replace the original QR code content. When doing this, be aware that only one
plugin may return such a value, and that e.g. the official check-in app will no longer
work.
''')

registration_form_deleted = _signals.signal('registration-form-deleted', '''
Called when a registration form is removed. The `sender` is the
`RegistrationForm` object.
''')

registration_form_field_deleted = _signals.signal('registration-form-field-deleted', '''
Called when a registration form field is removed. The `sender` is the
`RegistrationFormField` object.
''')

is_ticketing_handled = _signals.signal('is-ticketing-handled', '''
Called when resolving whether Indico should send tickets with e-mails
or it will be handled by other module. The `sender` is the
`RegistrationForm` object.

If this signal returns ``True``, no ticket will be emailed on registration.
''')

is_ticket_blocked = _signals.signal('is-ticket-blocked', '''
Called when resolving whether Indico should let a registrant download
their ticket.  The `sender` is the registrant's `Registration` object.

If this signal returns ``True``, the user will not be able to download
their ticket.  Any badge containing a ticket-specific placeholder such as
the ticket qr code is considered a ticket, and the restriction applies to
both users trying to get their own ticket and managers trying to get a
ticket for a registrant.
''')

is_field_data_locked = _signals.signal('is-field-data-locked', '''
Called when resolving whether Indico should let a data value be modified
in a registration. The participant's `Registration` is passed as `registration`.
The `sender` is the `RegistrationFormItem` object.

This signal returns a string containing the reason for the item being locked,
or `None` if the item is not locked.
''')

filter_selectable_badges = _signals.signal('filter-selectable-badges', '''
Called when composing lists of badge templates. The `sender` may be either
``BadgeSettingsForm``, ``RHListEventTemplates`` or ``RHListCategoryTemplates``.
The list of badge templates is passed in the `badge_templates` kwarg.
The signal handler is expected to mutate the list.
''')

before_check_registration_email = _signals.signal('before-check-registration-email', '''
Called before checking the validity of the registration email.  The sender is
the ``RegistrationForm`` object.  The signal handler is expected to return
``None`` if all checks passed or a ``{'status': ..., 'conflict': ...}``
dictionary.  ``'status'`` is expected to be either ``'error'``, ``'warning'`` or
``ok``.
''')

after_registration_form_clone = _signals.signal('after-registration-form-clone', '''
Executed after a registration form is cloned. The sender is the old ``RegistrationForm``
object being cloned. The new ``RegistrationForm`` object is passed in the ``new_form``
kwarg.
''')

generate_accompanying_person_id = _signals.signal('generate-accompanying-person-id', '''
Called after a permanent UUID is assigned to an accompanying person. The sender is the
``AccompanyingPersonSchema`` object. The temporary ID is passed in the ``temporary_id``
kwarg and the permanent UUID is passed in the ``permanent_id`` kwarg.
''')

registrant_list_action_menu = _signals.signal('registrant-list-action-menu', '''
Called when composing the list of menu items to be displayed under the "Actions" button
at the top of the list of registrants/participants. The `sender` is the corresponding
registration form.
''')

google_wallet_ticket_class_data = _signals.signal('google-wallet-ticket-class-data', '''
Called when data for a Google Wallet ticket class has been generated. The `sender` is the
`Event` object, the `data` kwarg contains the data that will be passed to the Google
Wallet API.
''')

google_wallet_ticket_object_data = _signals.signal('google-wallet-ticket-object-data', '''
Called when data for a Google Wallet ticket object has been generated. The `sender` is the
`Registration` object, the `data` kwarg contains the data that will be passed to the Google
Wallet API.
''')

apple_wallet_ticket_object = _signals.signal('apple-wallet-ticket-object', '''
Called when a ticket object for an Apple Wallet has been generated. The `sender` is the
`Event` object, the `obj` kwarg contains the Ticket object.
''')

apple_wallet_object = _signals.signal('apple-wallet-object', '''
Called when the Pass object for an Apple Wallet has been generated. The `sender` is the
`Registration` object, the `obj` kwarg contains the Pass object.
''')
