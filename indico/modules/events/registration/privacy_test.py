# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime, timedelta

import pytest
from pytz import utc

from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration.models.registrations import (PublishRegistrationsMode, Registration,
                                                                     RegistrationState, RegistrationVisibility)


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def assert_visibility(reg, visibility, test_visibility_prop=True):
    def _is_publishable_query(is_participant):
        return Registration.query.with_parent(reg.event).filter(Registration.is_publishable(is_participant)).has_rows()

    if test_visibility_prop:
        assert reg.visibility == visibility
    if visibility == RegistrationVisibility.nobody:
        assert not reg.is_publishable(True)
        assert not reg.is_publishable(False)
        assert not _is_publishable_query(True)
        assert not _is_publishable_query(False)
    elif visibility == RegistrationVisibility.participants:
        assert reg.is_publishable(True)
        assert not reg.is_publishable(False)
        assert _is_publishable_query(True)
        assert not _is_publishable_query(False)
    elif visibility == RegistrationVisibility.all:
        assert reg.is_publishable(True)
        assert reg.is_publishable(False)
        assert _is_publishable_query(True)
        assert _is_publishable_query(False)


@pytest.mark.usefixtures('dummy_reg')
def test_registration_visibility(dummy_event, dummy_regform):
    set_feature_enabled(dummy_event, 'registration', True)

    reg = dummy_event.registrations.one()

    assert dummy_regform.publish_registrations_public == PublishRegistrationsMode.hide_all
    assert dummy_regform.publish_registrations_participants == PublishRegistrationsMode.show_with_consent
    assert reg.consent_to_publish == RegistrationVisibility.nobody
    assert not reg.participant_hidden
    assert reg.is_active
    assert reg.state == RegistrationState.complete
    assert_visibility(reg, RegistrationVisibility.nobody)

    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.participants)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.participants)

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = RegistrationVisibility.nobody
    assert_visibility(reg, RegistrationVisibility.participants)
    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.participants)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.participants)

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.hide_all
    reg.consent_to_publish = RegistrationVisibility.nobody
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.nobody)

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_with_consent
    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_with_consent
    reg.consent_to_publish = RegistrationVisibility.nobody
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.participants)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.all)

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = RegistrationVisibility.nobody
    assert_visibility(reg, RegistrationVisibility.participants)
    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.participants)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.all)

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_all
    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = RegistrationVisibility.nobody
    assert_visibility(reg, RegistrationVisibility.all)
    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.all)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.all)

    reg.state = RegistrationState.rejected
    assert not reg.is_active
    assert_visibility(reg, RegistrationVisibility.nobody, test_visibility_prop=False)
    reg.state = RegistrationState.withdrawn
    assert not reg.is_active
    assert_visibility(reg, RegistrationVisibility.nobody, test_visibility_prop=False)
    reg.state = RegistrationState.pending
    assert reg.is_active
    assert_visibility(reg, RegistrationVisibility.nobody, test_visibility_prop=False)


@pytest.mark.usefixtures('dummy_reg')
def test_registration_visibility_hide_participants(dummy_event, dummy_regform):
    set_feature_enabled(dummy_event, 'registration', True)

    reg = dummy_event.registrations.one()
    reg.participant_hidden = True

    assert dummy_regform.publish_registrations_public == PublishRegistrationsMode.hide_all
    assert dummy_regform.publish_registrations_participants == PublishRegistrationsMode.show_with_consent
    assert reg.consent_to_publish == RegistrationVisibility.nobody
    assert reg.is_active
    assert reg.state == RegistrationState.complete
    assert_visibility(reg, RegistrationVisibility.nobody)

    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.nobody)

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = RegistrationVisibility.nobody
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.nobody)

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.hide_all
    reg.consent_to_publish = RegistrationVisibility.nobody
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.nobody)

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_with_consent
    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_with_consent
    reg.consent_to_publish = RegistrationVisibility.nobody
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.nobody)

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = RegistrationVisibility.nobody
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.nobody)

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_all
    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = RegistrationVisibility.nobody
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.participants
    assert_visibility(reg, RegistrationVisibility.nobody)
    reg.consent_to_publish = RegistrationVisibility.all
    assert_visibility(reg, RegistrationVisibility.nobody)

    reg.state = RegistrationState.rejected
    assert not reg.is_active
    assert_visibility(reg, RegistrationVisibility.nobody, test_visibility_prop=False)
    reg.state = RegistrationState.withdrawn
    assert not reg.is_active
    assert_visibility(reg, RegistrationVisibility.nobody, test_visibility_prop=False)
    reg.state = RegistrationState.pending
    assert reg.is_active
    assert_visibility(reg, RegistrationVisibility.nobody, test_visibility_prop=False)


@pytest.mark.usefixtures('dummy_reg')
def test_visibility_duration(dummy_event, dummy_regform, freeze_time):
    set_feature_enabled(dummy_event, 'registration', True)

    reg = dummy_event.registrations.one()
    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_all
    freeze_time(datetime(2022, 1, 1, tzinfo=utc))
    dummy_event.start_dt = datetime(2020, 1, 1, tzinfo=utc)
    dummy_event.end_dt = datetime(2021, 1, 1, tzinfo=utc)

    assert not reg.participant_hidden
    assert reg.is_active
    assert reg.state == RegistrationState.complete
    assert dummy_regform.publish_registrations_duration is None
    assert_visibility(reg, RegistrationVisibility.all)

    dummy_regform.publish_registrations_duration = timedelta(days=1*30)
    assert_visibility(reg, RegistrationVisibility.nobody, test_visibility_prop=False)
    dummy_regform.publish_registrations_duration = timedelta(days=12*30)
    assert_visibility(reg, RegistrationVisibility.nobody, test_visibility_prop=False)
    dummy_regform.publish_registrations_duration = timedelta(days=13*30)
    assert_visibility(reg, RegistrationVisibility.all)
    dummy_regform.publish_registrations_duration = timedelta(days=20*30)
    assert_visibility(reg, RegistrationVisibility.all)
