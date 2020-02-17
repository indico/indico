# This file is part of Indico.
# Copyright (C) 2002 - 2020 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db
from indico.modules.events.cloning import EventCloner
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration.models.registrations import Registration, RegistrationState


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def test_registration_clone(dummy_event, dummy_regform, create_event, dummy_user):
    set_feature_enabled(dummy_event, 'registration', True)

    reg1 = Registration(
        event_id=dummy_event.id,
        registration_form_id=dummy_regform.id,
        first_name="Guinea",
        last_name="Pig",
        checked_in=True,
        state=RegistrationState.complete,
        currency="USD",
        email="1337@example.com",
        user=dummy_user
    )
    dummy_event.registrations.append(reg1)
    db.session.flush()

    assert dummy_regform.event == dummy_event
    assert dummy_event.registrations.one().user == dummy_user
    assert dummy_event.registrations.one().checked_in

    copied_event = create_event()
    EventCloner.run_cloners(dummy_event, copied_event, {'registrations', 'registration_forms'})
    copied_registration = copied_event.registrations.one()

    assert copied_registration.event == copied_event
    assert copied_registration.user == dummy_user
    assert not copied_registration.checked_in
