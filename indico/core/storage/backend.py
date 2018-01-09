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
import sys
from contextlib import contextmanager
from hashlib import md5
from io import BytesIO
from tempfile import NamedTemporaryFile

from werkzeug.security import safe_join

from indico.core import signals
from indico.core.config import config
from indico.util.signals import named_objects_from_signal
from indico.util.string import return_ascii
from indico.web.flask.util import send_file


def get_storage(backend_name):
    """Returns an FS object for the given backend.

    The backend must be defined in the STORAGE_BACKENDS dict in the
    indico config.  Once a backend has been used it is assumed to
    stay there forever or at least as long as it is referenced
    somewhere.

    Each backend definition uses the ``name:data`` notation, e.g.
    ``fs:/some/folder/`` or ``foo:host=foo.host,token=secret``.
    """
    try:
        definition = config.STORAGE_BACKENDS[backend_name]
    except KeyError:
        raise RuntimeError('Storage backend does not exist: {}'.format(backend_name))
    name, data = definition.split(':', 1)
    try:
        backend = get_storage_backends()[name]
    except KeyError:
        raise RuntimeError('Storage backend {} has invalid type {}'.format(backend_name, name))
    return backend(data)


def get_storage_backends():
    return named_objects_from_signal(signals.get_storage_backends.send(), plugin_attr='plugin')


class StorageError(Exception):
    """Exception used when a storage operation fails for any reason"""


class StorageReadOnlyError(StorageError):
    """Exception used when trying to write to a read-only storage"""


class Storage(object):
    """Base class for storage backends

    To create a new storage backend, subclass this class and register
    it using the `get_storage_backends` signal.

    In case you wonder why both `save` and `send_file` require certain
    file metadata: Depending on the storage backend, the information
    needs to be set when saving the file (usually with external storage
    services such as S3) or provided when sending the file back to the
    client (for example if the file is accessed through the local file
    system).

    :param data: A string of data used to initialize the backend.
                 This could be a path, an url, or any other kind of
                 information needed by the backend.  If `simple_data`
                 is set, it should be a plain string. Otherwise it is
                 expected to be a string containing comma-separatey
                 key-value pairs: ``key=value,key2=value2,..``

    """
    #: unique name of the storage backend
    name = None
    #: plugin containing this backend - assigned automatically
    plugin = None
    #: if the backend uses a simple data string instead of key-value pairs
    simple_data = True

    def __init__(self, data):  # pragma: no cover
        pass

    def _parse_data(self, data):
        """Util to parse a key=value data string to a dict"""
        return dict((x.strip() for x in item.split('=', 1)) for item in data.split(',')) if data else {}

    def _ensure_fileobj(self, fileobj):
        """Ensures that fileobj is a file-like object and not a string"""
        return BytesIO(fileobj) if not hasattr(fileobj, 'read') else fileobj

    def _copy_file(self, source, target, chunk_size=1024*1024):
        """Copy a file, in chunks, from ``source`` to ``target``.

        The return value will be the MD5 checksum of the file (hex).
        """
        checksum = md5()
        while True:
            chunk = source.read(chunk_size)
            if not chunk:
                break
            target.write(chunk)
            checksum.update(chunk)
        return checksum.hexdigest().decode('ascii')

    def open(self, file_id):  # pragma: no cover
        """Opens a file in the storage for reading.

        This returns a file-like object which contains the content of
        the file.

        :param file_id: The ID of the file within the storage backend.
        """
        raise NotImplementedError

    @contextmanager
    def get_local_path(self, file_id):
        """Returns a local path for the file.

        While this path MAY point to the permanent location of the
        stored file, it MUST NOT be used for anything but read
        operations and MUST NOT be used after existing this function's
        contextmanager.

        :param file_id: The ID of the file within the storage backend.
        """
        with self.open(file_id) as fd:
            with NamedTemporaryFile(suffix='indico.tmp', dir=config.TEMP_DIR) as tmpfile:
                self._copy_file(fd, tmpfile)
                tmpfile.flush()
                yield tmpfile.name

    def save(self, name, content_type, filename, fileobj):  # pragma: no cover
        """Creates a new file in the storage.

        This returns a a string identifier which can be used later to
        retrieve the file from the storage.

        :param name: A unique name for the file.  This must be usable
                     as a filesystem path even though it depends on
                     the backend whether this name is used in such a
                     way or used at all.  It SHOULD not contain ``..``
                     as this could result in two apparently-different
                     names to actually end up being the same on
                     storage backends that use the regular file system.
                     Using slashes in the name is allowed, but when
                     doing so extra caution is needed to avoid cases
                     which fail on a filesystem backend such as trying
                     to save 'foo' and 'foo/bar.txt'
        :param content_type: The content-type of the file (may or may
                             not be used depending on the backend).
        :param filename: The original filename of the file, used e.g.
                         when sending the file to a client (may or may
                         not be used depending on the backend).
        :param fileobj: A file-like object containing the file data as
                        bytes or a bytestring.
        :return: (unicode, unicode) -- A tuple containing a unique
                        identifier for the file and an MD5 checksum.
        """
        raise NotImplementedError

    def delete(self, file_id):  # pragma: no cover
        """Deletes a file from the storage.

        :param file_id: The ID of the file within the storage backend.
        """
        raise NotImplementedError

    def getsize(self, file_id):  # pragma: no cover
        """Gets the size in bytes of a file

        :param file_id: The ID of the file within the storage backend.
        """
        raise NotImplementedError

    def send_file(self, file_id, content_type, filename, inline=True):  # pragma: no cover
        """Sends the file to the client.

        This returns a flask response that will eventually result in
        the user being offered to download the file (or view it in the
        browser).  Depending on the storage backend it may actually
        send a redirect to an external URL where the file is available.

        :param file_id: The ID of the file within the storage backend.
        :param content_type: The content-type of the file (may or may
                             not be used depending on the backend)
        :param filename: The file name to use when sending the file to
                         the client (may or may not be used depending
                         on the backend).
        :param inline: Whether the file should be displayed inline or
                       downloaded. Typically this will set the
                       Content-Disposition header. Depending on the
                       backend, this argument could be ignored.
        """
        raise NotImplementedError

    def __repr__(self):
        return '<{}()>'.format(type(self).__name__)


class ReadOnlyStorageMixin(object):
    """Mixin that makes write operations fail with an error"""

    def save(self, name, content_type, filename, fileobj):
        raise StorageReadOnlyError('Cannot write to read-only storage')

    def delete(self, file_id):
        raise StorageReadOnlyError('Cannot delete from read-only storage')


class FileSystemStorage(Storage):
    name = 'fs'
    simple_data = True

    def __init__(self, data):
        self.path = data

    def _resolve_path(self, path):
        full_path = safe_join(self.path, path)
        if full_path is None:
            raise ValueError('Invalid path: {}'.format(path))
        return full_path

    def open(self, file_id):
        try:
            return open(self._resolve_path(file_id), 'rb')
        except Exception as e:
            raise StorageError('Could not open "{}": {}'.format(file_id, e)), None, sys.exc_info()[2]

    @contextmanager
    def get_local_path(self, file_id):
        yield self._resolve_path(file_id)

    def save(self, name, content_type, filename, fileobj):
        try:
            fileobj = self._ensure_fileobj(fileobj)
            filepath = self._resolve_path(name)
            if os.path.exists(filepath):
                raise ValueError('A file with this name already exists')
            basedir = os.path.dirname(filepath)
            if not os.path.isdir(basedir):
                os.makedirs(basedir)
            with open(filepath, 'wb') as f:
                checksum = self._copy_file(fileobj, f)
            return name, checksum
        except Exception as e:
            raise StorageError('Could not save "{}": {}'.format(name, e)), None, sys.exc_info()[2]

    def delete(self, file_id):
        try:
            os.remove(self._resolve_path(file_id))
        except Exception as e:
            raise StorageError('Could not delete "{}": {}'.format(file_id, e)), None, sys.exc_info()[2]

    def getsize(self, file_id):
        try:
            return os.path.getsize(self._resolve_path(file_id))
        except Exception as e:
            raise StorageError('Could not get size of "{}": {}'.format(file_id, e)), None, sys.exc_info()[2]

    def send_file(self, file_id, content_type, filename, inline=True):
        try:
            return send_file(filename, self._resolve_path(file_id).encode('utf-8'), content_type, inline=inline)
        except Exception as e:
            raise StorageError('Could not send "{}": {}'.format(file_id, e)), None, sys.exc_info()[2]

    @return_ascii
    def __repr__(self):
        return '<FileSystemStorage: {}>'.format(self.path)


class ReadOnlyFileSystemStorage(ReadOnlyStorageMixin, FileSystemStorage):
    name = 'fs-readonly'

    @return_ascii
    def __repr__(self):
        return '<ReadOnlyFileSystemStorage: {}>'.format(self.path)


@signals.get_storage_backends.connect
def _get_storage_backends(sender, **kwargs):
    yield FileSystemStorage
    yield ReadOnlyFileSystemStorage


@signals.app_created.connect
def _check_storage_backends(app, **kwargs):
    # This will raise RuntimeError if the backend names are not unique
    get_storage_backends()
