# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.editing.models.revisions import FinalRevisionState, InitialRevisionState
from indico.modules.events.models.persons import EventPerson
from indico.modules.users.export import (get_abstracts, get_attachments, get_contributions, get_editables, get_papers,
                                         get_registration_data, get_subcontributions)
from indico.util.date_time import now_utc


pytest_plugins = ('indico.modules.events.registration.testing.fixtures',
                  'indico.modules.users.testing.fixtures')


@pytest.mark.usefixtures('dummy_reg_with_file_field')
def test_get_registration_data(dummy_user):
    data = get_registration_data(dummy_user)
    assert len(data) == 1
    assert data[0].filename == 'registration_upload.txt'


def test_get_get_attachments(db, dummy_user, create_user, dummy_event, create_attachment):
    attachments = get_attachments(dummy_user)
    assert not attachments

    creator = create_user(42)
    create_attachment(creator, dummy_event, title='Presentation')
    db.session.flush()

    attachments = get_attachments(dummy_user)
    assert not attachments

    attachment = create_attachment(dummy_user, dummy_event, title='Presentation')
    db.session.flush()
    attachments = get_attachments(dummy_user)
    assert attachments == [attachment]


def test_get_contributions(db, dummy_user, dummy_event, dummy_contribution):
    contribs = get_contributions(dummy_user)
    assert not contribs

    person = EventPerson.create_from_user(dummy_user, dummy_event)
    dummy_contribution.person_links.append(ContributionPersonLink(person=person))
    db.session.flush()

    contribs = get_contributions(dummy_user)
    assert contribs == [dummy_contribution]


def test_get_subcontributions(db, dummy_user, dummy_event, dummy_subcontribution):
    subcontribs = get_subcontributions(dummy_user)
    assert not subcontribs

    person = EventPerson.create_from_user(dummy_user, dummy_event)
    dummy_subcontribution.person_links.append(SubContributionPersonLink(person=person))
    db.session.flush()

    subcontribs = get_subcontributions(dummy_user)
    assert subcontribs == [dummy_subcontribution]


def test_get_abstracts_submitter(db, dummy_user, dummy_event, create_abstract):
    abstracts = get_abstracts(dummy_user)
    assert not abstracts

    abstract = create_abstract(dummy_event, 'Rewriting Indico in Rust', submitter=dummy_user)
    db.session.flush()
    abstracts = get_abstracts(dummy_user)
    assert abstracts == [abstract]


def test_get_abstracts_person_link(db, dummy_user, dummy_event, create_abstract):
    abstracts = get_abstracts(dummy_user)
    assert not abstracts

    abstract = create_abstract(dummy_event, 'IAAS: Indico As A Service', submitter=dummy_user)
    person = EventPerson.create_from_user(dummy_user, dummy_event)
    abstract.person_links.append(AbstractPersonLink(person=person, is_speaker=True))
    db.session.flush()

    abstracts = get_abstracts(dummy_user)
    assert abstracts == [abstract]


@pytest.mark.usefixtures('dummy_reg_with_file_field')
def test_get_papers_from_contribution_link(db, dummy_user, create_user, dummy_event,
                                           dummy_paper, create_paper_revision):
    papers = get_papers(dummy_user)
    assert not papers

    submitter = create_user(42)
    create_paper_revision(dummy_paper, submitter)
    db.session.flush()
    papers = get_papers(dummy_user)
    assert not papers

    person = EventPerson.create_from_user(dummy_user, dummy_event)
    dummy_paper.contribution.person_links.append(ContributionPersonLink(person=person))
    db.session.flush()

    papers = get_papers(dummy_user)
    assert len(papers) == 1
    assert papers[0].contribution == dummy_paper.contribution


@pytest.mark.usefixtures('dummy_reg_with_file_field')
def test_get_papers_from_paper_revision(db, dummy_user, dummy_paper, create_paper_revision):
    papers = get_papers(dummy_user)
    assert not papers

    create_paper_revision(dummy_paper, dummy_user)
    db.session.flush()

    papers = get_papers(dummy_user)
    assert len(papers) == 1
    assert papers[0].contribution == dummy_paper.contribution


def test_get_editables_from_contribution_link(db, dummy_event, dummy_user, create_user,
                                              dummy_editable, create_editing_revision):
    editables = get_editables(dummy_user)
    assert not editables

    submitter = create_user(42)
    create_editing_revision(dummy_editable, submitter, reviewed_dt=now_utc(),
                            initial_state=InitialRevisionState.ready_for_review,
                            final_state=FinalRevisionState.accepted)
    db.session.flush()
    editables = get_editables(dummy_user)
    assert not editables

    person = EventPerson.create_from_user(dummy_user, dummy_event)
    dummy_editable.contribution.person_links.append(ContributionPersonLink(person=person))
    db.session.flush()

    editables = get_editables(dummy_user)
    assert editables == [dummy_editable]


def test_get_editables_from_editing_revision(db, dummy_user, dummy_editable, create_editing_revision):
    editables = get_editables(dummy_user)
    assert not editables

    create_editing_revision(dummy_editable, dummy_user, reviewed_dt=now_utc(),
                            initial_state=InitialRevisionState.ready_for_review,
                            final_state=FinalRevisionState.accepted)
    db.session.flush()

    editables = get_editables(dummy_user)
    assert editables == [dummy_editable]
