# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.contributions.models.persons import (AuthorType, ContributionPersonLink,
                                                                SubContributionPersonLink)
from indico.modules.events.features.util import set_feature_enabled
from indico.modules.events.models.persons import EventPerson, EventPersonLink


def test_unused_event_person(db, dummy_user, dummy_event, create_contribution, create_subcontribution, create_abstract):
    person = EventPerson.create_from_user(dummy_user, event=dummy_event)
    assert not person.has_links

    dummy_event.person_links.append(EventPersonLink(person=person))
    db.session.flush()
    assert person.has_links

    dummy_event.person_links.clear()
    db.session.flush()
    assert not person.has_links

    set_feature_enabled(dummy_event, 'abstracts', True)
    abstract = create_abstract(dummy_event, 'Dummy abstract', submitter=dummy_user, person_links=[
        AbstractPersonLink(person=person, is_speaker=True, author_type=AuthorType.primary)
    ])
    assert person.has_links
    abstract.is_deleted = True
    assert not person.has_links

    contrib = create_contribution(dummy_event, 'Dummy contribution', person_links=[
        ContributionPersonLink(person=person, is_speaker=True)
    ])
    assert person.has_links
    contrib.is_deleted = True
    assert not person.has_links
    db.session.delete(contrib)

    contrib = create_contribution(dummy_event, 'Dummy contribution', person_links=[])
    assert not person.has_links
    create_subcontribution(contrib, 'Dummy subcontribution', person_links=[
        SubContributionPersonLink(person=person, is_speaker=True)
    ])
    assert person.has_links

    contrib.is_deleted = True
    assert not person.has_links

    db.session.delete(contrib)
    assert not person.has_links
