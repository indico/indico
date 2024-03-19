# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.contributions.lists import ContributionListGenerator
from indico.modules.events.contributions.models.persons import AuthorType, ContributionPersonLink
from indico.modules.events.models.persons import EventPerson


pytest_plugins = 'indico.modules.events.registration.testing.fixtures'


def test_filter_contrib_entries(app, dummy_event, create_user, create_contribution, dummy_regform, create_registration):
    registered_user = create_user(1)
    registered_speaker = create_user(2)
    unregistered_user = create_user(3)
    dummy_event.registrations.append(create_registration(registered_user, dummy_regform))
    dummy_event.registrations.append(create_registration(registered_speaker, dummy_regform))
    registered_speaker_contribution = create_contribution(dummy_event, 'Registered Speaker', person_links=[
        ContributionPersonLink(person=EventPerson.create_from_user(registered_speaker, dummy_event),
                               is_speaker=True)
    ])
    registered_speaker_author_contribution = create_contribution(
        dummy_event, 'Registered Speaker Author', person_links=[
            ContributionPersonLink(person=EventPerson.for_user(registered_speaker, dummy_event),
                                   is_speaker=True, author_type=AuthorType.primary)
        ])
    unregistered_speaker_registered_author_contribution = create_contribution(
        dummy_event, 'Unregistered Speaker, Registered Author', person_links=[
            ContributionPersonLink(person=EventPerson.for_user(unregistered_user, dummy_event),
                                   is_speaker=True),
            ContributionPersonLink(person=EventPerson.for_user(registered_user, dummy_event),
                                   author_type=AuthorType.primary)
        ])
    registered_speaker_unregistered_author_contribution = create_contribution(
        dummy_event, 'Registered Speaker, Unregistered Author', person_links=[
            ContributionPersonLink(person=EventPerson.for_user(registered_user, dummy_event), is_speaker=True),
            ContributionPersonLink(person=EventPerson.for_user(unregistered_user, dummy_event),
                                   author_type=AuthorType.primary)
        ])
    # Filter contributions with registered users
    with app.test_request_context():
        list_gen = ContributionListGenerator(dummy_event)
        list_gen.list_config['filters'] = {'extra': {'people': {'registered'}}}
        result = list_gen.get_list_kwargs()
    assert result['contribs'] == [
        registered_speaker_contribution,
        registered_speaker_author_contribution,
        unregistered_speaker_registered_author_contribution,
        registered_speaker_unregistered_author_contribution
    ]

    # Filter contributions with registered speakers
    list_gen.list_config['filters'] = {'extra': {'speakers': {'registered'}}}
    with app.test_request_context():
        result = list_gen.get_list_kwargs()
    assert result['contribs'] == [
        registered_speaker_contribution,
        registered_speaker_author_contribution,
        registered_speaker_unregistered_author_contribution
    ]

    # Filter contributions with unregistered speakers and registered users
    list_gen.list_config['filters'] = {'extra': {'speakers': {'not_registered'}, 'people': {'registered'}}}
    with app.test_request_context():
        result = list_gen.get_list_kwargs()
    assert result['contribs'] == [
        unregistered_speaker_registered_author_contribution
    ]
