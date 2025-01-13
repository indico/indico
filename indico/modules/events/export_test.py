# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import tarfile
import uuid
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

import pytest
import yaml

from indico.modules.attachments.util import get_attached_items
from indico.modules.events.contributions import Contribution
from indico.modules.events.export import export_event, import_event
from indico.modules.events.sessions import Session
from indico.testing.util import assert_yaml_snapshot
from indico.util.date_time import as_utc


class _MockUUID:
    def __init__(self):
        self.counter = 0

    def uuid4(self):
        u = uuid.UUID(int=self.counter, version=4)
        self.counter += 1
        return u


def _assert_yaml_snapshot(snapshot, data, name):
    __tracebackhide__ = True
    snapshot.snapshot_dir = Path(__file__).parent / 'tests'
    assert_yaml_snapshot(snapshot, data, name)


@pytest.fixture(autouse=True)
def reproducible_uuids(monkeypatch):
    muid = _MockUUID()
    monkeypatch.setattr('indico.modules.events.export.uuid4', muid.uuid4)


@pytest.fixture(autouse=True)
def no_verbose_iterator(monkeypatch):
    def _dummy(iterable, *args, **kwargs):
        yield from iterable

    monkeypatch.setattr('indico.modules.events.export.verbose_iterator', _dummy)


@pytest.fixture(autouse=True)
def static_versions(monkeypatch):
    monkeypatch.setattr('indico.__version__', '1.3.3.7')
    monkeypatch.setattr('indico.modules.events.export._get_alembic_version', lambda: ['feeddeadbeef'])


def test_event_export(db, dummy_event, monkeypatch, snapshot):
    monkeypatch.setattr('indico.modules.events.export.now_utc', lambda: as_utc(datetime(2017, 8, 24, 9, 0, 0)))

    f = BytesIO()
    dummy_event.created_dt = as_utc(datetime(2017, 8, 24, 0, 0, 0))
    dummy_event.start_dt = as_utc(datetime(2017, 8, 24, 10, 0, 0))
    dummy_event.end_dt = as_utc(datetime(2017, 8, 24, 12, 0, 0))

    s = Session(event=dummy_event, title='sd', is_deleted=True)
    Contribution(event=dummy_event, title='c1', duration=timedelta(minutes=30))
    Contribution(event=dummy_event, title='c2', session=s, duration=timedelta(minutes=30), is_deleted=True)
    db.session.flush()
    export_event(dummy_event, f)
    f.seek(0)

    # check composition of tarfile and data.yaml content
    with tarfile.open(fileobj=f) as tarf:
        assert tarf.getnames() == ['objects-1.yaml', 'data.yaml', 'ids.yaml']
        data = yaml.unsafe_load(tarf.extractfile('data.yaml'))
        _assert_yaml_snapshot(snapshot, data, 'export_test_1.yaml')
        objects = yaml.unsafe_load(tarf.extractfile('objects-1.yaml'))
        _assert_yaml_snapshot(snapshot, objects, 'export_test_1_objects.yaml')


@pytest.mark.usefixtures('dummy_attachment')
def test_event_attachment_export(db, dummy_event):
    s = Session(event=dummy_event, title='sd', is_deleted=True)
    Contribution(event=dummy_event, title='c1', duration=timedelta(minutes=30))
    Contribution(event=dummy_event, title='c2', session=s, duration=timedelta(minutes=30), is_deleted=True)
    db.session.flush()

    f = BytesIO()
    export_event(dummy_event, f)
    f.seek(0)

    with tarfile.open(fileobj=f) as tarf:
        data_file = tarf.extractfile('data.yaml')
        data = yaml.unsafe_load(data_file)
        objects_file = tarf.extractfile(data['object_files'][0])
        objs = yaml.unsafe_load(objects_file)
        event_uid = objs[0][2]['id'][1]

        # check that the exported metadata contains all the right objects
        assert [obj[0] for obj in objs] == ['events.events', 'events.sessions', 'events.contributions',
                                            'events.contributions', 'attachments.folders', 'attachments.attachments',
                                            'attachments.files']
        # check that the attached file's metadata is included
        assert objs[5][2]['title'] == 'dummy_attachment'
        assert objs[5][2]['folder_id'] is not None
        assert objs[4][2]['title'] == 'dummy_folder'
        assert objs[4][2]['linked_event_id'][1] == event_uid
        file_ = objs[6][2]['__file__'][1]
        assert file_['filename'] == 'dummy_file.txt'
        assert file_['content_type'] == 'text/plain'
        assert file_['size'] == 11
        assert file_['md5'] == '5eb63bbbe01eeed093cb22bb8f5acdc3'
        # check that the file itself was included (and verify content)
        assert tarf.getnames() == ['00000000-0000-4000-8000-000000000013', 'objects-1.yaml', 'data.yaml', 'ids.yaml']
        assert tarf.extractfile('00000000-0000-4000-8000-000000000013').read() == b'hello world'


def test_event_import(db, dummy_user):
    data_yaml_content = (Path(__file__).parent / 'tests' / 'export_test_2.yaml').read_text()
    objects_yaml_content = (Path(__file__).parent / 'tests' / 'export_test_2_objects.yaml').read_text()
    data_yaml = BytesIO(data_yaml_content.encode())
    objects_yaml = BytesIO(objects_yaml_content.encode())
    tar_buffer = BytesIO()

    # User should be matched by e-mail
    dummy_user.email = '1337@example.test'
    db.session.flush()

    # create a tar file artificially, using the provided YAML
    with tarfile.open(mode='w', fileobj=tar_buffer) as tarf:
        tar_info = tarfile.TarInfo('data.yaml')
        tar_info.size = len(data_yaml_content)
        tarf.addfile(tar_info, data_yaml)
        tar_info = tarfile.TarInfo('objects-1.yaml')
        tar_info.size = len(objects_yaml_content)
        tarf.addfile(tar_info, objects_yaml)
        tar_info = tarfile.TarInfo('00000000-0000-4000-8000-00000000001c')
        tar_info.size = 11
        tarf.addfile(tar_info, BytesIO(b'hello world'))

    tar_buffer.seek(0)
    e = import_event(tar_buffer, create_users=False)[0]
    # Check that event metadata is fine
    assert e.title == 'dummy#0'
    assert e.creator == dummy_user
    assert e.created_dt == as_utc(datetime(2017, 8, 24, 15, 28, 42, 652626))
    assert e.start_dt == as_utc(datetime(2017, 8, 24, 10, 0, 0))
    assert e.end_dt == as_utc(datetime(2017, 8, 24, 12, 0, 0))
    # Check that attachment metadata is fine
    assert get_attached_items(e)['files'] == []
    folder = get_attached_items(e)['folders'][0]
    assert folder.title == 'dummy_folder'
    attachment = folder.attachments[0]
    assert attachment.title == 'dummy_attachment'
    # Check that the actual file is accessible
    assert attachment.file.open().read() == b'hello world'
