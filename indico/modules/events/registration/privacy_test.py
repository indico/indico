# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration.models.registrations import (PublishRegistrationsMode, Registration,
                                                                     RegistrationState)


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.mark.usefixtures('dummy_reg')
def test_registration_publishable(dummy_event, dummy_regform):
    set_feature_enabled(dummy_event, 'registration', True)

    reg = dummy_event.registrations.one()

    assert dummy_regform.publish_registrations_public == PublishRegistrationsMode.hide_all
    assert dummy_regform.publish_registrations_participants == PublishRegistrationsMode.show_with_consent
    assert not reg.consented_to_publish
    assert reg.is_active
    assert reg.state == RegistrationState.complete
    assert not reg.is_publishable

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_all
    assert reg.is_publishable

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_with_consent
    assert not reg.is_publishable

    reg.consented_to_publish = True
    assert reg.is_publishable


@pytest.mark.usefixtures('dummy_reg')
def test_registration_publishable_query(dummy_event, dummy_regform):
    set_feature_enabled(dummy_event, 'registration', True)

    def _get_publishable():
        return Registration.query.with_parent(dummy_event).filter(Registration.is_publishable)

    reg = dummy_event.registrations.one()

    assert dummy_regform.publish_registrations_public == PublishRegistrationsMode.hide_all
    assert dummy_regform.publish_registrations_participants == PublishRegistrationsMode.show_with_consent
    assert not reg.consented_to_publish
    assert reg.is_active
    assert reg.state == RegistrationState.complete
    assert not _get_publishable().has_rows()

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_all
    assert _get_publishable().has_rows()

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_with_consent
    assert not _get_publishable().has_rows()

    reg.consented_to_publish = True
    assert _get_publishable().has_rows()
