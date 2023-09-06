# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import datetime
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from indico.modules.files.models.files import File
from indico.modules.users.models.export import DataExportOptions, DataExportRequest, DataExportRequestState
from indico.modules.users.tasks import _get_old_requests, build_storage_path, export_user_data, generate_zip, get_data
from indico.util.date_time import now_utc


pytest_plugins = ('indico.modules.events.registration.testing.fixtures',
                  'indico.modules.users.testing.fixtures')


@pytest.fixture(scope='function')
def mock_io(mocker):
    class MockBytesIO(BytesIO):
        name = '/tmp/somefile'  # for temp_file.name

        def __init__(self, *args, **kwargs):  # for NamedTemporaryFile constructor
            super().__init__()

    # We don't want to write to the disk
    mocker.patch('indico.modules.users.tasks.NamedTemporaryFile', MockBytesIO)
    # We don't want to delete anything from the disk either
    mocker.patch.object(Path, 'unlink')


@pytest.fixture
def all_data_yamls():
    options_map = {
        DataExportOptions.contribs: ('contributions', 'subcontributions'),
        DataExportOptions.abstracts_papers: ('abstracts', 'papers'),
        DataExportOptions.misc: ('miscellaneous',),
    }
    yamls = []
    for opt in DataExportOptions:
        yamls.extend(options_map.get(opt, (opt.name,)))
    return [f'{x}.yaml' for x in yamls]


def test_build_storage_path(dummy_reg_with_file_field, dummy_attachment, dummy_abstract_file,
                            dummy_paper_file, dummy_editing_revision_file):
    path = build_storage_path(dummy_reg_with_file_field.data[0])
    assert path == 'registrations/0_dummy0/43_73_registration_upload.txt'

    path = build_storage_path(dummy_attachment.file)
    assert path == 'attachments/42_dummy_file.txt'

    path = build_storage_path(dummy_abstract_file)
    assert path == ('abstracts/0_dummy0/42_Broken_Symmetry_and_the_Mass_of_Gauge_Vector_Mesons/'
                    '42_dummy_abstract_file.txt')

    path = build_storage_path(dummy_paper_file)
    assert path == 'papers/0_dummy0/42_Dummy_Contribution/42_dummy_file.txt'

    path = build_storage_path(dummy_editing_revision_file)
    assert path == 'editables/paper/0_dummy0/42_Dummy_Contribution/42_dummy_file.txt'


def test_get_data(dummy_user):
    request = DataExportRequest(user=dummy_user, selected_options=list(DataExportOptions))
    data = get_data(request)
    assert isinstance(data, dict)


def test_get_data_convert_options_to_fields(mocker, dummy_user):
    mock = mocker.patch('indico.modules.users.schemas.UserDataExportSchema')

    request = DataExportRequest(user=dummy_user, selected_options=[DataExportOptions.contribs])
    get_data(request)
    mock.assert_called_with(only=['contributions', 'subcontributions'])
    mock.reset_mock()

    request = DataExportRequest(user=dummy_user, selected_options=list(DataExportOptions))
    get_data(request)
    mock.assert_called_with(only=['personal_data', 'settings', 'contributions', 'subcontributions',
                                  'registrations', 'room_booking', 'abstracts', 'papers',
                                  'survey_submissions', 'attachments', 'editables', 'miscellaneous'])


def test_generate_zip_no_files(dummy_user):
    request = DataExportRequest(user=dummy_user, selected_options=[DataExportOptions.personal_data])
    buffer = BytesIO()
    generate_zip(request, buffer, max_size=0)
    buffer.seek(0)

    zip = ZipFile(buffer)
    assert zip.namelist() == ['personal_data.yaml']


@pytest.mark.usefixtures('dummy_attachment', 'dummy_abstract_file', 'dummy_paper_file',
                         'dummy_editing_revision_file', 'dummy_reg_with_file_field')
def test_generate_zip_all_options(dummy_user, all_data_yamls):
    request = DataExportRequest(user=dummy_user, selected_options=list(DataExportOptions))
    buffer = BytesIO()
    generate_zip(request, buffer, max_size=100_000_000)
    buffer.seek(0)

    zip = ZipFile(buffer)
    assert zip.namelist() == [
        *all_data_yamls,
        'attachments/42_dummy_file.txt',
        ('abstracts/0_dummy0/42_Broken_Symmetry_and_the_Mass_of_Gauge_Vector_Mesons/'
         '42_dummy_abstract_file.txt'),
        'papers/0_dummy0/42_Dummy_Contribution/42_dummy_file.txt',
        'editables/paper/0_dummy0/42_Dummy_Contribution/42_dummy_file.txt',
        'registrations/0_dummy0/43_73_registration_upload.txt'
    ]


@pytest.mark.usefixtures('dummy_attachment')
def test_generate_zip_max_size_exceeds_1(dummy_user, all_data_yamls):
    request = DataExportRequest(user=dummy_user, selected_options=list(DataExportOptions))
    buffer = BytesIO()
    generate_zip(request, buffer, max_size=0)
    buffer.seek(0)

    zip = ZipFile(buffer)
    # max_size is set 0, so only the data file should be exported
    assert request.max_size_exceeded
    assert zip.namelist() == all_data_yamls


@pytest.mark.usefixtures('dummy_abstract_file')
def test_generate_zip_max_size_exceeds_2(dummy_user, dummy_attachment, all_data_yamls):
    request = DataExportRequest(user=dummy_user, selected_options=list(DataExportOptions))
    # Set max_size to cover only the attachment, but no the abstract file
    buffer = BytesIO()
    generate_zip(request, buffer, max_size=dummy_attachment.file.size)
    buffer.seek(0)

    zip = ZipFile(buffer)
    # Only the attachment should be exported
    assert request.max_size_exceeded
    assert zip.namelist() == [*all_data_yamls, 'attachments/42_dummy_file.txt',]


@pytest.mark.usefixtures('mock_io')
def test_export_user_data(mocker, dummy_user):
    success = mocker.patch('indico.modules.users.tasks.notify_data_export_success')
    failure = mocker.patch('indico.modules.users.tasks.notify_data_export_failure')

    options = [DataExportOptions.personal_data]
    export_user_data(dummy_user, options)

    failure.assert_not_called()
    success.assert_called_with(dummy_user.data_export_request)
    assert dummy_user.data_export_request.state == DataExportRequestState.success
    assert dummy_user.data_export_request.selected_options == options

    file = File.query.filter(File.filename == 'data-export.zip').first()
    with file.open() as f:
        zip = ZipFile(f)
        assert zip.namelist() == ['personal_data.yaml']


@pytest.mark.usefixtures('mock_io', 'dummy_attachment', 'dummy_abstract_file', 'dummy_paper_file',
                         'dummy_editing_revision_file', 'dummy_reg_with_file_field')
def test_export_user_data_all_options(mocker, dummy_user, all_data_yamls):
    success = mocker.patch('indico.modules.users.tasks.notify_data_export_success')
    failure = mocker.patch('indico.modules.users.tasks.notify_data_export_failure')

    options = list(DataExportOptions)
    export_user_data(dummy_user, options)

    failure.assert_not_called()
    success.assert_called_with(dummy_user.data_export_request)
    assert dummy_user.data_export_request.state == DataExportRequestState.success
    assert dummy_user.data_export_request.selected_options == options

    file = File.query.filter(File.filename == 'data-export.zip').first()
    with file.open() as f:
        zip = ZipFile(f)
        assert zip.namelist() == [
            *all_data_yamls,
            'attachments/42_dummy_file.txt',
            ('abstracts/0_dummy0/42_Broken_Symmetry_and_the_Mass_of_Gauge_Vector_Mesons/'
             '42_dummy_abstract_file.txt'),
            'papers/0_dummy0/42_Dummy_Contribution/42_dummy_file.txt',
            'editables/paper/0_dummy0/42_Dummy_Contribution/42_dummy_file.txt',
            'registrations/0_dummy0/43_73_registration_upload.txt'
        ]


@pytest.mark.usefixtures('mock_io')
def test_export_user_data_existing_request(mocker, db, dummy_user):
    mock = mocker.patch('indico.modules.users.tasks.generate_zip')

    DataExportRequest(user=dummy_user, selected_options=[],
                      state=DataExportRequestState.running)
    db.session.flush()
    export_user_data(dummy_user, options=[])
    mock.assert_not_called()


@pytest.mark.usefixtures('mock_io')
def test_export_user_data_zip_error(mocker, dummy_user):
    success = mocker.patch('indico.modules.users.tasks.notify_data_export_success')
    failure = mocker.patch('indico.modules.users.tasks.notify_data_export_failure')

    def raises(*args, **kwargs):
        raise Exception('Failed to generate zip')
    mocker.patch('indico.modules.users.tasks.generate_zip', raises)

    export_user_data(dummy_user, list(DataExportOptions))
    failure.assert_called()
    success.assert_not_called()


@pytest.mark.usefixtures('mock_io')
def test_export_user_data_file_claim_error(mocker, dummy_user):
    success = mocker.patch('indico.modules.users.tasks.notify_data_export_success')
    failure = mocker.patch('indico.modules.users.tasks.notify_data_export_failure')

    def raises(*args, **kwargs):
        raise Exception('Failed to claim file')
    mocker.patch.object(File, 'claim', raises)

    export_user_data(dummy_user, list(DataExportOptions))
    failure.assert_called()
    success.assert_not_called()


def test__get_old_requests(db, dummy_user, create_file):
    assert not _get_old_requests(days=10)
    file = create_file('test.txt', 'user', 'text/plain', 'data')
    request_success = DataExportRequest(user=dummy_user, selected_options=[],
                                        requested_dt=datetime(2000, 5, 22, 12, 0, 0),
                                        state=DataExportRequestState.success,
                                        file=file)
    db.session.flush()
    assert _get_old_requests(days=10) == [request_success]

    db.session.delete(request_success)
    db.session.flush()
    file = create_file('test.txt', 'user', 'text/plain', 'data')
    request_success = DataExportRequest(user=dummy_user, selected_options=[],
                                        requested_dt=now_utc(),
                                        state=DataExportRequestState.success,
                                        file=file)
    db.session.flush()
    assert not _get_old_requests(days=10)

    db.session.delete(request_success)
    db.session.flush()
    DataExportRequest(user=dummy_user, selected_options=[],
                      requested_dt=now_utc(),
                      state=DataExportRequestState.failed)
    assert not _get_old_requests(days=10)
