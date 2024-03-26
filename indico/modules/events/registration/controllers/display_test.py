# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from flask import request, session
from werkzeug.exceptions import Forbidden, UnprocessableEntity

from indico.modules.events.registration.controllers.display import (RHRegistrationDisplayEdit, RHRegistrationForm,
                                                                    RHRegistrationWithdraw)
from indico.modules.events.registration.controllers.management.fields import _fill_form_field_with_data
from indico.modules.events.registration.models.form_fields import RegistrationFormField
from indico.modules.events.registration.models.forms import ModificationMode
from indico.modules.events.registration.models.invitations import RegistrationInvitation
from indico.modules.events.registration.models.items import RegistrationFormSection
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.modules.events.registration.util import create_registration
from indico.testing.util import extract_emails
from indico.util.date_time import now_utc


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.mark.usefixtures('request_context')
def test_RHRegistrationForm_can_register(db, dummy_regform, dummy_reg, dummy_user, create_user):
    invitation = RegistrationInvitation(registration_form=dummy_regform, email='foo@bar.com', first_name='foo',
                                        last_name='bar', affiliation='test')
    db.session.flush()
    request.view_args = {'reg_form_id': dummy_regform.id, 'event_id': dummy_regform.event_id}
    request.args = {'invitation': invitation.uuid}
    rh = RHRegistrationForm()
    rh._process_args()
    assert rh._can_register()  # invited
    rh.invitation = None
    assert not rh._can_register()  # not open
    dummy_regform.start_dt = now_utc(False)
    assert rh._can_register()
    session.set_session_user(dummy_user)  # registered in dummy_reg
    assert not rh._can_register()
    dummy_reg.state = RegistrationState.rejected
    assert not rh._can_register()  # being rejected does not allow registering again
    dummy_reg.state = RegistrationState.withdrawn
    assert not rh._can_register()  # being withdrawn does not allow registering again
    session.set_session_user(create_user(123, email='user@example.com'))
    assert rh._can_register()
    dummy_regform.registration_limit = 1
    assert rh._can_register()  # withdrawn/rejected do not count against limit
    dummy_reg.state = RegistrationState.complete
    db.session.expire(dummy_regform)
    assert not rh._can_register()  # exceeding limit


@pytest.mark.usefixtures('request_context')
def test_withdraw_registration_rh(smtp, dummy_regform, dummy_reg, dummy_user):
    # Register the user and enable manager notifications
    dummy_regform.start_dt = now_utc(False)
    dummy_regform.manager_notifications_enabled = True
    dummy_regform.manager_notification_recipients = ['mgr@example.test']
    session.set_session_user(dummy_user)

    # Set up request
    request.view_args = {
        'reg_form_id': dummy_regform.id,
        'event_id': dummy_regform.event_id,
    }
    rh = RHRegistrationWithdraw()
    rh._process_args()

    # Throw forbidden if no modification allowed
    dummy_regform.modification_mode = ModificationMode.not_allowed
    assert not dummy_reg.can_be_withdrawn
    with pytest.raises(Forbidden):
        rh._check_access()
    dummy_regform.modification_mode = ModificationMode.allowed_always

    # Check if an email is sent, one to the user, one to the manager
    assert not smtp.outbox
    rh._process()
    extract_emails(
        smtp,
        required=True,
        count=1,
        subject=f'[Indico] Registration withdrawn for {dummy_regform.event.title}',
        to=dummy_user.email,
    )
    extract_emails(
        smtp,
        required=True,
        count=1,
        subject='[Indico] Registration withdrawn for {}: {} {}'.format(  # noqa: UP032
            dummy_regform.event.title, dummy_user.first_name, dummy_user.last_name
        ),
        to='mgr@example.test',
    )
    assert not smtp.outbox


def test_display_edit_override_required_rh(
    db, dummy_regform, dummy_user, app_context, smtp
):
    # Add a section and a required field
    section = RegistrationFormSection(
        registration_form=dummy_regform, title='dummy_section', is_manager_only=False
    )

    assert dummy_regform.active_registration_count == 0
    boolean_field = RegistrationFormField(parent_id=section.id, registration_form=dummy_regform)
    _fill_form_field_with_data(
        boolean_field, {'input_type': 'bool', 'is_required': True, 'title': 'Yes/No'}
    )

    # Register the user
    dummy_regform.modification_mode = ModificationMode.allowed_always
    data = {
        'email': dummy_user.email,
        'first_name': dummy_user.first_name,
        'last_name': dummy_user.last_name,
    }
    reg = create_registration(
        dummy_regform, data, invitation=None, management=False, notify_user=False
    )
    assert dummy_regform.active_registration_count == 1

    # We are not a manager, but are attempting to avoid setting the required field. We should get a 422
    jsondata = {'first_name': 'hax0r', 'override_required': True}
    url = f'/event/{dummy_regform.event_id}/registrations/{dummy_regform.id}/edit?token={reg.uuid}'
    with app_context.test_request_context(url, json=jsondata):
        rh = RHRegistrationDisplayEdit()
        rh._process_args()
        rh._check_access()

        with pytest.raises(UnprocessableEntity) as excinfo:
            rh._process_POST()

        messages = excinfo.value.data['messages']
        assert len(messages) == 2
        assert messages['override_required'][0] == 'Unknown field.'
        assert messages[boolean_field.html_field_name][0] == 'Missing data for required field.'

    # Try again with the correct fields
    assert not smtp.outbox
    del jsondata['override_required']
    jsondata[boolean_field.html_field_name] = True
    with app_context.test_request_context(url, json=jsondata):
        rh = RHRegistrationDisplayEdit()
        rh._process_args()
        rh._check_access()
        rh._process_POST()

        assert reg.first_name == 'hax0r'
        assert reg.data_by_field[boolean_field.id].data is True

        extract_emails(
            smtp,
            required=True,
            count=1,
            subject=f'[Indico] Registration modified for {dummy_regform.event.title}',
            to=dummy_user.email,
        )
