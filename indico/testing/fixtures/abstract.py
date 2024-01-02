# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.abstracts.models.abstracts import Abstract
from indico.modules.events.abstracts.models.files import AbstractFile
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.contributions.models.persons import AuthorType
from indico.modules.users.models.users import UserTitle


@pytest.fixture
def create_abstract(db):
    """Return a callable that lets you create an abstract."""

    def _create_abstract(event, title, **kwargs):
        abstract = Abstract(event=event, title=title, **kwargs)
        db.session.add(abstract)
        db.session.flush()
        return abstract

    return _create_abstract


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
def dummy_abstract(db, dummy_event, dummy_user, create_dummy_person):
    """Create a dummy abstract."""
    abstract = Abstract(id=420,
                        friendly_id=314,
                        title='Broken Symmetry and the Mass of Gauge Vector Mesons',
                        event=dummy_event,
                        submitter=dummy_user,
                        locator={'event_id': -314, 'abstract_id': 1234},
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
def create_abstract_file():
    """Return a callable which lets you create an abstract file."""
    def _create_abstract_file(abstract, filename, content_type, data, **kwargs):
        file_ = AbstractFile(filename=filename, content_type=content_type, abstract=abstract, **kwargs)
        file_.save(data.encode())
        return file_

    return _create_abstract_file


@pytest.fixture
def dummy_abstract_file(dummy_abstract, create_abstract_file):
    """Create a dummy abstract file."""
    return create_abstract_file(dummy_abstract, id=420, filename='dummy_abstract_file.txt',
                                content_type='text/plain', data='A dummy file')
