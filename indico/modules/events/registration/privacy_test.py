# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.registration.models.registrations import (PublishConsentType, PublishRegistrationsMode,
                                                                     Registration, RegistrationState)


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


@pytest.mark.usefixtures('dummy_reg')
def test_registration_publishable(dummy_event, dummy_regform):
    set_feature_enabled(dummy_event, 'registration', True)

    reg = dummy_event.registrations.one()

    assert dummy_regform.publish_registrations_public == PublishRegistrationsMode.hide_all
    assert dummy_regform.publish_registrations_participants == PublishRegistrationsMode.show_with_consent
    assert reg.consent_to_publish == PublishConsentType.not_given
    assert reg.is_active
    assert reg.state == RegistrationState.complete
    assert not reg.is_publishable(True)
    assert not reg.is_publishable(False)

    reg.consent_to_publish = PublishConsentType.participants
    assert reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.all
    assert reg.is_publishable(True)
    assert not reg.is_publishable(False)

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = PublishConsentType.not_given
    assert reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.participants
    assert reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.all
    assert reg.is_publishable(True)
    assert not reg.is_publishable(False)

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.hide_all
    reg.consent_to_publish = PublishConsentType.not_given
    assert not reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.participants
    assert not reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.all
    assert not reg.is_publishable(True)
    assert not reg.is_publishable(False)

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_with_consent
    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_with_consent
    reg.consent_to_publish = PublishConsentType.not_given
    assert not reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.participants
    assert reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.all
    assert reg.is_publishable(True)
    assert reg.is_publishable(False)

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = PublishConsentType.not_given
    assert reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.participants
    assert reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.all
    assert reg.is_publishable(True)
    assert reg.is_publishable(False)

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_all
    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = PublishConsentType.not_given
    assert reg.is_publishable(True)
    assert reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.participants
    assert reg.is_publishable(True)
    assert reg.is_publishable(False)
    reg.consent_to_publish = PublishConsentType.all
    assert reg.is_publishable(True)
    assert reg.is_publishable(False)

    reg.state = RegistrationState.rejected
    assert not reg.is_active
    assert not reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.state = RegistrationState.withdrawn
    assert not reg.is_active
    assert not reg.is_publishable(True)
    assert not reg.is_publishable(False)
    reg.state = RegistrationState.pending
    assert reg.is_active
    assert not reg.is_publishable(True)
    assert not reg.is_publishable(False)


@pytest.mark.usefixtures('dummy_reg')
def test_registration_publishable_query(dummy_event, dummy_regform):
    set_feature_enabled(dummy_event, 'registration', True)

    def _get_publishable(is_participant):
        return Registration.query.with_parent(dummy_event).filter(Registration.is_publishable(is_participant))

    reg = dummy_event.registrations.one()

    assert dummy_regform.publish_registrations_public == PublishRegistrationsMode.hide_all
    assert dummy_regform.publish_registrations_participants == PublishRegistrationsMode.show_with_consent
    assert not reg.consent_to_publish
    assert reg.is_active
    assert reg.state == RegistrationState.complete
    assert not _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()

    reg.consent_to_publish = PublishConsentType.participants
    assert _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.all
    assert _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = PublishConsentType.not_given
    assert _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.participants
    assert _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.all
    assert _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.hide_all
    reg.consent_to_publish = PublishConsentType.not_given
    assert not _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.participants
    assert not _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.all
    assert not _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_with_consent
    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_with_consent
    reg.consent_to_publish = PublishConsentType.not_given
    assert not _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.participants
    assert _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.all
    assert _get_publishable(True).has_rows()
    assert _get_publishable(False).has_rows()

    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = PublishConsentType.not_given
    assert _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.participants
    assert _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.all
    assert _get_publishable(True).has_rows()
    assert _get_publishable(False).has_rows()

    dummy_regform.publish_registrations_public = PublishRegistrationsMode.show_all
    dummy_regform.publish_registrations_participants = PublishRegistrationsMode.show_all
    reg.consent_to_publish = PublishConsentType.not_given
    assert _get_publishable(True).has_rows()
    assert _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.participants
    assert _get_publishable(True).has_rows()
    assert _get_publishable(False).has_rows()
    reg.consent_to_publish = PublishConsentType.all
    assert _get_publishable(True).has_rows()
    assert _get_publishable(False).has_rows()

    reg.state = RegistrationState.rejected
    assert not reg.is_active
    assert not _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.state = RegistrationState.withdrawn
    assert not reg.is_active
    assert not _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
    reg.state = RegistrationState.pending
    assert reg.is_active
    assert not _get_publishable(True).has_rows()
    assert not _get_publishable(False).has_rows()
