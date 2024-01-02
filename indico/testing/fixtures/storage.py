# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from hashlib import md5
from io import BytesIO

import pytest

from indico.core import signals
from indico.core.storage.backend import Storage
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.files.models.files import File


@signals.core.get_storage_backends.connect
def _get_storage_backends(sender, **kwargs):
    return MemoryStorage


class MemoryStorage(Storage):
    name = 'mem'
    files = {}

    def _get_file_content(self, file_id):
        return self.files[file_id][2]

    def open(self, file_id):
        return BytesIO(self._get_file_content(file_id))

    def save(self, file_id, content_type, filename, fileobj):
        data = self._ensure_fileobj(fileobj).read()
        self.files[file_id] = (content_type, filename, data)
        return file_id, md5(data).hexdigest()

    def delete(self, file_id):
        del self.files[file_id]

    def getsize(self, file_id):
        return len(self._get_file_content(file_id))


@pytest.fixture
def create_attachment(db):
    """Return a callable which lets you create attachments."""
    def _create_attachment(user, object, title, attachment_folder_id=None, attachment_file_id=None, **kwargs):
        folder = AttachmentFolder(id=attachment_folder_id, object=object, title='dummy_folder',
                                  description='a dummy folder')
        file = AttachmentFile(user=user, filename='dummy_file.txt', content_type='text/plain', id=attachment_file_id)
        attachment = Attachment(folder=folder, user=user, type=AttachmentType.file, file=file, title=title, **kwargs)
        file.save(b'hello world')
        db.session.flush()
        return attachment
    return _create_attachment


@pytest.fixture
def dummy_attachment(dummy_user, dummy_event, create_attachment):
    """Create a dummy attachment."""
    return create_attachment(dummy_user, dummy_event, title='dummy_attachment', description='Dummy attachment',
                             id=420, attachment_folder_id=420, attachment_file_id=420)


@pytest.fixture
def create_file(db):
    """Return a callable which lets you create (unclaimed) files."""
    def _create_file(filename, content_type, context, data, **kwargs):
        file = File(filename=filename, content_type=content_type, **kwargs)
        file.save(context, data.encode())
        db.session.add(file)
        db.session.flush()
        return file
    return _create_file


@pytest.fixture
def dummy_file(create_file):
    """Create a dummy (unclaimed) file."""
    return create_file('dummy_file.txt', 'text/plain', 'dummy_context', 'A dummy file', id=420)
