# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import pytest

from indico.modules.events.abstracts.models.abstracts import Abstract, AbstractState
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.abstracts.models.email_templates import AbstractEmailTemplate
from indico.modules.events.abstracts.notifications import send_abstract_notifications
from indico.modules.events.abstracts.util import build_default_email_template
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.users.models.users import UserTitle


@pytest.fixture
def create_dummy_person(db, create_event_person):
    def _create(abstract, first_name, last_name, email, affiliation, title, is_speaker, author_type):
        person = create_event_person(abstract.event_new, first_name=first_name, last_name=last_name, email=email,
                                     affiliation=affiliation, title=title)
        link = AbstractPersonLink(abstract=abstract, person=person, is_speaker=is_speaker, author_type=author_type)
        db.session.add(person)
        db.session.flush()
        return link
    return _create


@pytest.fixture
def dummy_abstract(db, dummy_contribution, dummy_user, create_dummy_person):
    abstract = Abstract(friendly_id=314,
                        title="Broken Symmetry and the Mass of Gauge Vector Mesons",
                        event_new=dummy_contribution.event_new,
                        submitter=dummy_user,
                        contribution=dummy_contribution,
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


def test_accept_abstract(mocker, dummy_abstract, create_email_template):
    send_email = mocker.patch('indico.modules.events.abstracts.notifications.send_email')
    event = dummy_abstract.event_new

    event.abstract_email_templates.append(
        create_email_template(event, 0, 'accept', 'accept', [{'state': 'accepted'}], True))

    send_abstract_notifications(dummy_abstract)
    assert send_email.call_count == 0

    dummy_abstract.state = AbstractState.accepted
    send_abstract_notifications(dummy_abstract)
    assert send_email.call_count == 0
