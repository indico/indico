# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import pytest
from flask import request, session

from indico.modules.events.registration.controllers.display import RHRegistrationForm
from indico.modules.events.registration.models.invitations import RegistrationInvitation
from indico.modules.events.registration.models.registrations import RegistrationState
from indico.util.date_time import now_utc


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.mark.usefixtures('request_context')
def test_RHRegistrationForm_can_register(db, dummy_regform, dummy_reg, dummy_user, create_user):
    invitation = RegistrationInvitation(registration_form=dummy_regform, email='foo@bar.com', first_name='foo',
                                        last_name='bar', affiliation='test')
    db.session.flush()
    request.view_args = {'reg_form_id': dummy_regform.id, 'confId': dummy_regform.event_id}
    request.args = {'invitation': invitation.uuid}
    rh = RHRegistrationForm()
    rh._process_args()
    assert rh._can_register()  # invited
    rh.invitation = None
    assert not rh._can_register()  # not open
    dummy_regform.start_dt = now_utc(False)
    assert rh._can_register()
    session.user = dummy_user  # registered in dummy_reg
    assert not rh._can_register()
    dummy_reg.state = RegistrationState.rejected
    assert not rh._can_register()  # being rejected does not allow registering again
    dummy_reg.state = RegistrationState.withdrawn
    assert not rh._can_register()  # being withdrawn does not allow registering again
    session.user = create_user(123, email='user@example.com')
    assert rh._can_register()
    dummy_regform.registration_limit = 1
    assert rh._can_register()  # withdrawn/rejected do not count against limit
    dummy_reg.state = RegistrationState.complete
    assert not rh._can_register()  # exceeding limit
