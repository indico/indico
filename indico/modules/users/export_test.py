# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from indico.core.config import config
from indico.core.db import db
from indico.modules.events.abstracts.models.persons import AbstractPersonLink
from indico.modules.events.contributions.models.persons import ContributionPersonLink, SubContributionPersonLink
from indico.modules.events.editing.models.revisions import RevisionType
from indico.modules.events.models.persons import EventPerson
from indico.modules.files.models.files import File
from indico.modules.users.export import (build_storage_path, convert_to_yaml, export_user_data, get_abstracts,
                                         get_attachments, get_contributions, get_editables, get_old_requests,
                                         get_papers, get_registration_documents, get_registration_files,
                                         get_subcontributions, options_to_fields, serialize_user_data)
from indico.modules.users.models.export import DataExportOptions, DataExportRequest, DataExportRequestState
from indico.util.date_time import now_utc


pytest_plugins = ('indico.modules.events.registration.testing.fixtures',
                  'indico.modules.users.testing.fixtures')


@pytest.fixture
def mock_io(mocker):
    class MockNamedTemporaryFile(BytesIO):
        name = '/tmp/somefile'  # noqa: S108

        def __init__(self, *args, **kwargs):
            super().__init__()

    # We don't want to write to the disk
    mocker.patch('indico.modules.users.export.NamedTemporaryFile', MockNamedTemporaryFile)
    # We don't want to delete anything from the disk either
    mocker.patch.object(Path, 'unlink')


@pytest.fixture
def all_data_yamls():
    fields = options_to_fields(list(DataExportOptions))
    return [f'{x}.yaml' for x in fields]


@pytest.mark.usefixtures('mock_io')
def test_export_user_data_existing_request(mocker, db, dummy_user):
    mock = mocker.patch('indico.modules.users.export.generate_zip')

    DataExportRequest(user=dummy_user, selected_options=[], state=DataExportRequestState.running)
    db.session.flush()
    export_user_data(dummy_user, options=[], include_files=False)
    mock.assert_not_called()


@pytest.mark.usefixtures('mock_io')
def test_export_user_data_error(mocker, dummy_user):
    success = mocker.patch('indico.modules.users.export.notify_data_export_success')
    failure = mocker.patch('indico.modules.users.export.notify_data_export_failure')

    def raises(*args, **kwargs):
        raise Exception('Mock exception')
    mocker.patch('indico.modules.users.export.generate_zip', raises)

    export_user_data(dummy_user, options=[], include_files=False)
    assert dummy_user.data_export_request.state == DataExportRequestState.failed
    failure.assert_called()
    success.assert_not_called()


@pytest.mark.usefixtures('mock_io', 'dummy_attachment', 'dummy_abstract_file', 'dummy_paper_file',
                         'dummy_editing_revision_file', 'dummy_reg_with_file_field')
def test_export_user_data(mocker, dummy_user, all_data_yamls):
    success = mocker.patch('indico.modules.users.export.notify_data_export_success')
    failure = mocker.patch('indico.modules.users.export.notify_data_export_failure')

    options = list(DataExportOptions)
    export_user_data(dummy_user, options, include_files=True)

    assert dummy_user.data_export_request.state == DataExportRequestState.success
    assert dummy_user.data_export_request.selected_options == options
    assert not dummy_user.data_export_request.max_size_exceeded
    failure.assert_not_called()
    success.assert_called_with(dummy_user.data_export_request)

    file = File.query.filter(File.filename == 'data-export.zip').first()
    with file.open() as f:
        zip_file = ZipFile(f)
        assert zip_file.namelist() == [
            *all_data_yamls,
            'attachments/420_dummy_file.txt',
            ('abstracts/0_dummy0/420_Broken_Symmetry_and_the_Mass_of_Gauge_Vector_Mesons/'
             '420_dummy_abstract_file.txt'),
            'papers/0_dummy0/420_Dummy_Contribution/420_dummy_file.txt',
            'editables/paper/0_dummy0/420_Dummy_Contribution/420_dummy_file.txt',
            'registrations/0_dummy0/730_730_registration_upload.txt'
        ]


@pytest.mark.usefixtures('mock_io', 'dummy_attachment', 'dummy_abstract_file', 'dummy_paper_file',
                         'dummy_editing_revision_file', 'dummy_reg_with_file_field')
def test_export_user_data_no_files(mocker, dummy_user, all_data_yamls):
    success = mocker.patch('indico.modules.users.export.notify_data_export_success')
    failure = mocker.patch('indico.modules.users.export.notify_data_export_failure')

    options = list(DataExportOptions)
    export_user_data(dummy_user, options, include_files=False)

    assert dummy_user.data_export_request.state == DataExportRequestState.success
    assert dummy_user.data_export_request.selected_options == options
    assert not dummy_user.data_export_request.max_size_exceeded
    failure.assert_not_called()
    success.assert_called_with(dummy_user.data_export_request)

    file = File.query.filter(File.filename == 'data-export.zip').first()
    with file.open() as f:
        zip_file = ZipFile(f)
        assert zip_file.namelist() == all_data_yamls


@pytest.mark.usefixtures('dummy_attachment')
def test_export_user_data_max_size_exceeded_1(mocker, dummy_user, all_data_yamls):
    class MockConfig:
        def __getattr__(self, name):
            if name == 'MAX_DATA_EXPORT_SIZE':
                # Only the yaml files should be exported and no additional files
                return 0
            return getattr(config, name)

    mocker.patch('indico.modules.users.export.config', MockConfig())
    success = mocker.patch('indico.modules.users.export.notify_data_export_success')
    failure = mocker.patch('indico.modules.users.export.notify_data_export_failure')

    options = list(DataExportOptions)
    export_user_data(dummy_user, options, include_files=True)

    assert dummy_user.data_export_request.state == DataExportRequestState.success
    assert dummy_user.data_export_request.selected_options == options
    assert dummy_user.data_export_request.max_size_exceeded
    failure.assert_not_called()
    success.assert_called_with(dummy_user.data_export_request)

    file = File.query.filter(File.filename == 'data-export.zip').first()
    with file.open() as f:
        zip_file = ZipFile(f)
        assert zip_file.namelist() == all_data_yamls


@pytest.mark.usefixtures('dummy_abstract_file')
def test_export_user_data_max_size_exceeded_2(mocker, dummy_user, dummy_attachment, all_data_yamls):
    class MockConfig:
        def __getattr__(self, name):
            if name == 'MAX_DATA_EXPORT_SIZE':
                # Set max_size so that the attachment fits, but the abstract file does not
                return dummy_attachment.file.size / 1024**2
            return getattr(config, name)

    mocker.patch('indico.modules.users.export.config', MockConfig())
    success = mocker.patch('indico.modules.users.export.notify_data_export_success')
    failure = mocker.patch('indico.modules.users.export.notify_data_export_failure')

    options = list(DataExportOptions)
    export_user_data(dummy_user, options, include_files=True)

    assert dummy_user.data_export_request.state == DataExportRequestState.success
    assert dummy_user.data_export_request.selected_options == options
    assert dummy_user.data_export_request.max_size_exceeded
    failure.assert_not_called()
    success.assert_called_with(dummy_user.data_export_request)

    file = File.query.filter(File.filename == 'data-export.zip').first()
    with file.open() as f:
        zip_file = ZipFile(f)
        assert zip_file.namelist() == [*all_data_yamls, 'attachments/420_dummy_file.txt']


def test_serialize_user_data(dummy_user):
    request = DataExportRequest(user=dummy_user, selected_options=[DataExportOptions.contribs])
    data = serialize_user_data(request)
    assert set(data.keys()) == {'contributions', 'subcontributions'}

    db.session.delete(request)
    db.session.flush()

    request = DataExportRequest(user=dummy_user, selected_options=list(DataExportOptions))
    data = serialize_user_data(request)
    assert set(data.keys()) == {'personal_data', 'settings', 'contributions', 'subcontributions', 'registrations',
                                'room_booking', 'survey_submissions', 'abstracts', 'papers', 'miscellaneous',
                                'editables', 'attachments', 'note_revisions'}


@pytest.mark.usefixtures('dummy_reg_with_file_field')
def test_get_registration_files(dummy_user):
    files = get_registration_files(dummy_user)
    assert len(files) == 1
    assert files[0].filename == 'registration_upload.txt'


def test_get_registration_documents(dummy_user, create_receipt_file, dummy_reg, dummy_event_template):
    create_receipt_file(dummy_reg, dummy_event_template)
    create_receipt_file(dummy_reg, dummy_event_template, published=False)
    files = get_registration_documents(dummy_user)
    assert len(files) == 1
    assert files[0].is_published
    assert files[0].file.filename == 'test.pdf'


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
    create_editing_revision(dummy_editable, submitter, created_dt=now_utc(), type=RevisionType.acceptance)
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

    create_editing_revision(dummy_editable, dummy_user, created_dt=now_utc(), type=RevisionType.acceptance)
    db.session.flush()

    editables = get_editables(dummy_user)
    assert editables == [dummy_editable]


def test_build_storage_path(dummy_reg_with_file_field, dummy_attachment, dummy_abstract_file,
                            dummy_paper_file, dummy_editing_revision_file):
    path = build_storage_path(dummy_reg_with_file_field.data[0])
    assert path == 'registrations/0_dummy0/730_730_registration_upload.txt'

    path = build_storage_path(dummy_attachment.file)
    assert path == 'attachments/420_dummy_file.txt'

    path = build_storage_path(dummy_abstract_file)
    assert path == ('abstracts/0_dummy0/420_Broken_Symmetry_and_the_Mass_of_Gauge_Vector_Mesons/'
                    '420_dummy_abstract_file.txt')

    path = build_storage_path(dummy_paper_file)
    assert path == 'papers/0_dummy0/420_Dummy_Contribution/420_dummy_file.txt'

    path = build_storage_path(dummy_editing_revision_file)
    assert path == 'editables/paper/0_dummy0/420_Dummy_Contribution/420_dummy_file.txt'


def test_convert_to_yaml():
    data = {'foo': [1, 2, {'bar': [3, 4]}]}
    string = convert_to_yaml(data)

    assert string == '''\
foo:
  - 1
  - 2
  - bar:
      - 3
      - 4
'''


def test_get_old_requests(db, dummy_user, create_file):
    assert not get_old_requests(days=10)
    file = create_file('test.txt', 'user', 'text/plain', 'data')
    request_success = DataExportRequest(user=dummy_user, selected_options=[],
                                        requested_dt=datetime(2000, 5, 22, 12, 0, 0),
                                        state=DataExportRequestState.success,
                                        file=file)
    db.session.flush()
    assert get_old_requests(days=10) == [request_success]

    db.session.delete(request_success)
    db.session.flush()
    file = create_file('test.txt', 'user', 'text/plain', 'data')
    request_success = DataExportRequest(user=dummy_user, selected_options=[],
                                        requested_dt=now_utc(),
                                        state=DataExportRequestState.success,
                                        file=file)
    db.session.flush()
    assert not get_old_requests(days=10)

    db.session.delete(request_success)
    db.session.flush()
    DataExportRequest(user=dummy_user, selected_options=[],
                      requested_dt=now_utc(),
                      state=DataExportRequestState.failed)
    assert not get_old_requests(days=10)
