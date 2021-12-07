# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.contributions.lists import ContributionListGenerator
from indico.modules.events.contributions.models.persons import ContributionPersonLink
from indico.modules.events.models.persons import EventPerson
from indico.modules.events.registration.models.forms import RegistrationForm
from indico.modules.events.registration.models.registrations import Registration, RegistrationState


@pytest.fixture
def create_registration(dummy_event):
    """Return a callable that lets you create a contribution."""

    def _create_registration(user, regform, **kwargs):
        return Registration(
            first_name='Guinea',
            last_name='Pig',
            checked_in=True,
            state=RegistrationState.complete,
            currency='USD',
            email=user.email,
            user=user,
            registration_form=regform,
            **kwargs
        )

    return _create_registration


def test_filter_contrib_entries(app, db, dummy_event, create_user, create_contribution, create_registration):
    registered_user = create_user(1)
    registered_speaker = create_user(2)
    unregistered_user = create_user(3)
    dummy_regform = RegistrationForm(event=dummy_event, title='Registration Form', currency='USD')
    dummy_event.registrations.append(create_registration(registered_user, dummy_regform))
    dummy_event.registrations.append(create_registration(registered_speaker, dummy_regform))
    registered_contribution = create_contribution(dummy_event, 'Registered User', person_links=[
        ContributionPersonLink(person=EventPerson.create_from_user(registered_user, dummy_event))
    ])
    speaker_contribution = create_contribution(dummy_event, 'Registered Speaker', person_links=[
        ContributionPersonLink(person=EventPerson.create_from_user(registered_speaker, dummy_event),
                               is_speaker=True)
    ])
    create_contribution(dummy_event, 'Unregistered User', person_links=[
        ContributionPersonLink(person=EventPerson.create_from_user(unregistered_user, dummy_event))
    ])
    # Filter contributions with registered users
    with app.test_request_context():
        list_gen = ContributionListGenerator(dummy_event)
        list_gen.list_config['filters'] = {'items': {'people': {'registered'}}}
        result = list_gen.get_list_kwargs()
    assert result['contribs'] == [registered_contribution, speaker_contribution]

    # Filter contributions with registered speakers
    list_gen.list_config['filters'] = {'items': {'speakers': {'registered'}}}
    with app.test_request_context():
        result = list_gen.get_list_kwargs()
    assert result['contribs'] == [speaker_contribution]
