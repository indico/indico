# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import os
import tarfile
import uuid
from datetime import datetime, timedelta
from io import BytesIO

import pytest
import yaml

from indico.core.db.sqlalchemy.links import LinkType
from indico.modules.attachments.util import get_attached_items
from indico.modules.events.contributions import Contribution
from indico.modules.events.export import export_event, import_event
from indico.modules.events.sessions import Session
from indico.util.date_time import as_utc


class _MockUUID(object):
    def __init__(self):
        self.counter = 0

    def uuid4(self):
        u = uuid.UUID(int=self.counter, version=4)
        self.counter += 1
        return u


@pytest.fixture
def reproducible_uuids(monkeypatch):
    muid = _MockUUID()
    monkeypatch.setattr('indico.modules.events.export.uuid4', muid.uuid4)


@pytest.fixture
def static_indico_version(monkeypatch):
    monkeypatch.setattr('indico.__version__', b'1.3.3.7')


@pytest.mark.usefixtures('reproducible_uuids', 'static_indico_version')
def test_event_export(db, dummy_event, monkeypatch):
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

    with open(os.path.join(os.path.dirname(__file__), 'export_test_1.yaml'), 'r') as ref_file:
        data_yaml_content = ref_file.read()

    # check composition of tarfile and data.yaml content
    with tarfile.open(fileobj=f) as tarf:
        assert tarf.getnames() == ['data.yaml']
        assert tarf.extractfile('data.yaml').read() == data_yaml_content


@pytest.mark.usefixtures('reproducible_uuids')
def test_event_attachment_export(db, dummy_event, dummy_attachment):
    s = Session(event=dummy_event, title='sd', is_deleted=True)
    Contribution(event=dummy_event, title='c1', duration=timedelta(minutes=30))
    Contribution(event=dummy_event, title='c2', session=s, duration=timedelta(minutes=30), is_deleted=True)

    dummy_attachment.folder.event = dummy_event
    dummy_attachment.folder.linked_event = dummy_event
    dummy_attachment.folder.link_type = LinkType.event

    dummy_attachment.file.save(BytesIO(b'hello world'))
    db.session.flush()

    f = BytesIO()
    export_event(dummy_event, f)
    f.seek(0)

    with tarfile.open(fileobj=f) as tarf:
        data_file = tarf.extractfile('data.yaml')
        data = yaml.load(data_file)
        objs = data['objects']
        event_uid = objs[0][1]['id'][1]

        # check that the exported metadata contains all the right objects
        assert [obj[0] for obj in objs] == [u'events.events', u'events.sessions', u'events.contributions',
                                            u'events.contributions', u'attachments.folders', u'attachments.attachments',
                                            u'attachments.files']
        # check that the attached file's metadata is included
        assert objs[5][1]['title'] == 'dummy_attachment'
        assert objs[5][1]['folder_id'] is not None
        assert objs[4][1]['title'] == 'dummy_folder'
        assert objs[4][1]['linked_event_id'][1] == event_uid
        file_ = objs[6][1]['__file__'][1]
        assert file_['filename'] == 'dummy_file.txt'
        assert file_['content_type'] == 'text/plain'
        assert file_['size'] == 11
        assert file_['md5'] == '5eb63bbbe01eeed093cb22bb8f5acdc3'
        # check that the file itself was included (and verify content)
        assert tarf.getnames() == ['00000000-0000-4000-8000-000000000013', 'data.yaml']
        assert tarf.extractfile('00000000-0000-4000-8000-000000000013').read() == 'hello world'


@pytest.mark.usefixtures('static_indico_version')
def test_event_import(db, dummy_user):
    with open(os.path.join(os.path.dirname(__file__), 'export_test_2.yaml'), 'r') as ref_file:
        data_yaml_content = ref_file.read()

    data_yaml = BytesIO(data_yaml_content.encode('utf-8'))
    tar_buffer = BytesIO()

    # User should be matched by e-mail
    dummy_user.email = '1337@example.com'
    db.session.flush()

    # create a tar file artificially, using the provided YAML
    with tarfile.open(mode='w', fileobj=tar_buffer) as tarf:
        tar_info = tarfile.TarInfo('data.yaml')
        tar_info.size = len(data_yaml_content)
        tarf.addfile(tar_info, data_yaml)
        tar_info = tarfile.TarInfo('00000000-0000-4000-8000-00000000001c')
        tar_info.size = 11
        tarf.addfile(tar_info, BytesIO(b'hello world'))

    tar_buffer.seek(0)
    e = import_event(tar_buffer, create_users=False)
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
    assert attachment.file.open().read() == 'hello world'
