# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import re

import pytest

from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.notifications import send_abstract_notifications
from indico.modules.events.abstracts.util import build_default_email_template
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.events.contributions.models.types import ContributionType
from indico.modules.events.tracks.models.tracks import Track
from indico.modules.users.models.users import UserTitle
from indico.util.date_time import now_utc


def assert_text_equal(v1, v2):
    """Compare two strings, ignoring white space and line breaks."""
    assert re.sub(r'\s', '', v1) == re.sub(r'\s', '', v2)


@pytest.fixture
def create_dummy_person(db, create_event_person):
    def _create(abstract, first_name, last_name, email, affiliation, title, is_speaker, author_type):
        person = create_event_person(abstract.event, first_name=first_name, last_name=last_name, email=email,
                                     affiliation=affiliation, title=title)
        link = AbstractPersonLink(abstract=abstract, person=person, is_speaker=is_speaker, author_type=author_type)
        db.session.add(person)
        db.session.flush()
        return link
    return _create


@pytest.fixture
def create_dummy_track(db):
    def _create(event):
        track = Track(title='Dummy Track', event=event)
        db.session.add(track)
        db.session.flush()
        return track
    return _create


@pytest.fixture
def create_dummy_contrib_type(db):
    def _create(event, name='Poster'):
        contrib_type = ContributionType(name=name, event=event)
        db.session.add(contrib_type)
        db.session.flush()
        return contrib_type
    return _create


@pytest.fixture
def dummy_abstract(db, dummy_event, dummy_user, create_dummy_person):
    abstract = Abstract(friendly_id=314,
                        title="Broken Symmetry and the Mass of Gauge Vector Mesons",
                        event=dummy_event,
                        submitter=dummy_user,
                        locator={'confId': -314, 'abstract_id': 1234},
                        judgment_comment='Vague but interesting!')

    author1 = create_dummy_person(abstract, 'John', 'Doe', 'doe@example.com', 'ACME', UserTitle.mr, True,
                                  AuthorType.primary)
    author2 = create_dummy_person(abstract, 'Pocahontas', 'Silva', 'pocahontas@example.com', 'ACME', UserTitle.prof,
                                  False, AuthorType.primary)
    coauthor1 = create_dummy_person(abstract, 'John', 'Smith', 'smith@example.com', 'ACME', UserTitle.dr, False,
                                    AuthorType.primary)

    abstract.person_links = [author1, author2, coauthor1]
    db.session.add(abstract)
    db.session.flush()
    return abstract


@pytest.fixture
def create_email_template(db):
    def _create(event, position, tpl_type, title, rules, stop_on_match):
        tpl = build_default_email_template(event, tpl_type)
        tpl.position = position
        tpl.title = title
        tpl.rules = rules
        tpl.stop_on_match = stop_on_match
        return tpl
    return _create


@pytest.fixture
def abstract_objects(dummy_abstract, create_dummy_contrib_type, create_dummy_track):
    event = dummy_abstract.event
    return event, dummy_abstract, create_dummy_track(event), create_dummy_contrib_type(event)


@pytest.mark.usefixtures('request_context')
def test_abstract_notification(mocker, abstract_objects, create_email_template, dummy_user):
    send_email = mocker.patch('indico.modules.events.abstracts.notifications.send_email')

    event, abstract, track, contrib_type = abstract_objects

    event.abstract_email_templates.append(
        create_email_template(event, 0, 'accept', 'accepted', [{'state': [AbstractState.accepted.value]}], True))

    send_abstract_notifications(abstract)
    assert send_email.call_count == 0

    abstract.accepted_contrib_type = contrib_type
    abstract.state = AbstractState.accepted
    abstract.judge = dummy_user
    abstract.judgment_dt = now_utc(False)
    send_abstract_notifications(abstract)
    assert send_email.call_count == 1


@pytest.mark.usefixtures('request_context')
def test_notification_rules(mocker, abstract_objects, create_email_template, dummy_user, dummy_event):
    send_email = mocker.patch('indico.modules.events.abstracts.notifications.send_email')

    event, abstract, track, contrib_type = abstract_objects
    event.abstract_email_templates.append(
        create_email_template(event, 0, 'merge', 'merged poster for track', [
            {'state': [AbstractState.merged.value], 'track': [track.id]}
        ], True))

    send_abstract_notifications(abstract)
    assert send_email.call_count == 0

    abstract.state = AbstractState.accepted
    abstract.judge = dummy_user
    abstract.judgment_dt = now_utc(False)
    abstract.accepted_track = track
    send_abstract_notifications(abstract)
    assert send_email.call_count == 0

    abstract.state = AbstractState.merged
    abstract.merged_into = Abstract(title='test', submitter=dummy_user, event=dummy_event)
    abstract.accepted_track = None
    abstract.submitted_for_tracks = {track}
    send_abstract_notifications(abstract)
    assert send_email.call_count == 1


@pytest.mark.usefixtures('request_context')
def test_notification_several_conditions(db, mocker, abstract_objects, create_email_template, create_dummy_track,
                                         create_dummy_contrib_type, dummy_user):
    event, abstract, track, contrib_type = abstract_objects
    event.abstract_email_templates = [
        create_email_template(event, 0, 'accept', 'accepted', [
            {'state': [AbstractState.accepted.value], 'track': [track.id], 'contribution_type': [contrib_type.id]},
            {'state': [AbstractState.accepted.value], 'contribution_type': []}
        ], True)
    ]

    send_email = mocker.patch('indico.modules.events.abstracts.notifications.send_email')
    abstract.state = AbstractState.accepted
    abstract.judge = dummy_user
    abstract.judgment_dt = now_utc(False)
    abstract.accepted_track = track
    send_abstract_notifications(abstract)
    assert send_email.call_count == 1

    send_email.reset_mock()
    abstract.accepted_contrib_type = contrib_type
    send_abstract_notifications(abstract)
    assert send_email.call_count == 1

    send_email.reset_mock()
    abstract.accepted_track = create_dummy_track(event)
    abstract.accepted_contrib_type = create_dummy_contrib_type(event, name='Presentation')
    db.session.flush()
    send_abstract_notifications(abstract)
    assert send_email.call_count == 0


@pytest.mark.usefixtures('request_context')
def test_notification_any_conditions(mocker, abstract_objects, create_email_template, dummy_user):
    event, abstract, track, contrib_type = abstract_objects
    event.abstract_email_templates = [
        create_email_template(event, 0, 'accept', 'accepted', [
            {'state': [AbstractState.accepted.value]}
        ], True)
    ]

    send_email = mocker.patch('indico.modules.events.abstracts.notifications.send_email')
    abstract.state = AbstractState.accepted
    abstract.judge = dummy_user
    abstract.judgment_dt = now_utc(False)
    abstract.accepted_track = track
    send_abstract_notifications(abstract)
    assert send_email.call_count == 1


@pytest.mark.usefixtures('request_context')
def test_notification_stop_on_match(mocker, abstract_objects, create_email_template, dummy_user):
    event, abstract, track, contrib_type = abstract_objects
    event.abstract_email_templates = [
        create_email_template(event, 0, 'accept', 'accepted poster', [
            {'state': [AbstractState.accepted.value]}
        ], False),
        create_email_template(event, 0, 'accept', 'accepted poster 2', [
            {'state': [AbstractState.accepted.value]}
        ], True)
    ]

    send_email = mocker.patch('indico.modules.events.abstracts.notifications.send_email')
    abstract.state = AbstractState.accepted
    abstract.judge = dummy_user
    abstract.judgment_dt = now_utc(False)
    send_abstract_notifications(abstract)
    assert send_email.call_count == 2

    send_email.reset_mock()
    event.abstract_email_templates[0].stop_on_match = True
    send_abstract_notifications(abstract)
    assert send_email.call_count == 1


@pytest.mark.usefixtures('request_context')
def test_email_content(monkeypatch, abstract_objects, create_email_template, dummy_user):
    def _mock_send_email(email, event, module, user):
        assert event == ev
        assert module == 'Abstracts'
        assert email['subject'] == '[Indico] Abstract Acceptance notification (#314)'
        assert_text_equal(email['body'], """
            Dear Guinea Pig,

            We're pleased to announce that your abstract "Broken Symmetry and the Mass of Gauge Vector Mesons" with ID
            #314 has been accepted in track "Dummy Track" (Poster).

            See below a summary of your submitted abstract:
            Conference: {event.title}
            Submitted by: Guinea Pig
            Title: Broken Symmetry and the Mass of Gauge Vector Mesons
            Primary Authors: John Doe, Pocahontas Silva, John Smith
            Co-authors:
            Track classification: Dummy Track
            Presentation type: Poster

            For a more detailed summary please visit the page of your abstract:
            http://localhost/event/-314/abstracts/1234/

            Kind regards,
            The organizers of {event.title}

            --
            Indico :: Call for Abstracts
            http://localhost/event/{event.id}/
        """.format(event=ev))

    ev, abstract, track, contrib_type = abstract_objects
    monkeypatch.setattr('indico.modules.events.abstracts.notifications.send_email', _mock_send_email)

    ev.abstract_email_templates.append(
        create_email_template(ev, 0, 'accept', 'accept', [{'state': [AbstractState.accepted.value]}], True))

    abstract.accepted_contrib_type = contrib_type
    abstract.accepted_track = track
    abstract.state = AbstractState.accepted
    abstract.judge = dummy_user
    abstract.judgment_dt = now_utc(False)
    send_abstract_notifications(abstract)
