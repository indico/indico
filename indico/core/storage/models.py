# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

"""
Mixins that provide inheriting classes with the basic columns and
relationships for non-DB storage of files.

``StoredFileMixin`` defines a pointer to a "physical" file that exists in some
kind of storage backend. As for ``VersionedResourceMixin``, it allows do define
an abstract resource with multiple versions (files). This allows for (very)
rudimentary version control. Inheriting classes will be responsible for
specifying, among others, which storage backend to use.
"""


from __future__ import unicode_literals

from sqlalchemy.event import listen
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.storage.backend import get_storage
from indico.util.date_time import now_utc


class VersionedResourceMixin(object):

    # Class that will inherit from StoredFileMixin
    stored_file_class = None
    # Foreign key that, from such a class, will point here
    stored_file_fkey = None

    @staticmethod
    def _add_file_to_relationship(target, value, *unused):
        if value is None:
            # we don't allow file<->link conversions so setting it to None is pointless
            # and would just break integrity
            raise ValueError('file cannot be set to None')
        with db.session.no_autoflush:
            target.all_files.append(value)

    @classmethod
    def register_versioned_resource_events(cls):
        """Register SQLAlchemy events. Should be called
           right after class definition."""
        listen(cls.file, 'set', cls._add_file_to_relationship)

    #: The ID of the latest file for a file resource
    @declared_attr
    def file_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey(cls.stored_file_class.__table__.fullname + '.id', use_alter=True),
            nullable=True
        )

    #: The currently active file for the resource
    @declared_attr
    def file(cls):
        return db.relationship(
            cls.stored_file_class,
            primaryjoin=lambda: cls.file_id == cls.stored_file_class.id,
            foreign_keys=lambda: cls.file_id,
            lazy=False,
            post_update=True
        )

    #: The list of all files for the resource
    @declared_attr
    def all_files(cls):
        return db.relationship(
            cls.stored_file_class,
            primaryjoin=lambda: cls.id == getattr(cls.stored_file_class, cls.stored_file_fkey),
            foreign_keys=lambda: getattr(cls.stored_file_class, cls.stored_file_fkey),
            lazy=True,
            cascade='all, delete, delete-orphan',
            order_by=lambda: cls.stored_file_class.created_dt.desc(),
            backref=db.backref(
                getattr(cls.stored_file_class, 'version_of'),
                lazy=False
            )
        )


class StoredFileMixin(object):
    #: Name of attribute (backref) that will be made to point
    #: to the versioned resource (leave as ``None`` if you
    #: don't want versioning)
    version_of = None
    #: Whether to track the creation time.  This is required when
    #: using versioning!
    add_file_date_column = True
    #: Whether a row must always contain a file
    file_required = True

    @declared_attr
    def filename(cls):
        """The name of the file"""
        return db.Column(
            db.String,
            nullable=not cls.file_required
        )

    @declared_attr
    def content_type(cls):
        """The MIME type of the file"""
        return db.Column(
            db.String,
            nullable=not cls.file_required
        )

    @declared_attr
    def size(cls):
        """
        The size of the file (in bytes).

        Automatically assigned when `save()` is called.
        """
        return db.Column(
            db.BigInteger,
            nullable=not cls.file_required
        )

    @declared_attr
    def storage_backend(cls):
        return db.Column(
            db.String,
            nullable=not cls.file_required
        )

    @declared_attr
    def storage_file_id(cls):
        return db.Column(
            db.String,
            nullable=not cls.file_required
        )

    @declared_attr
    def created_dt(cls):
        """The date/time when the file was uploaded"""
        if not cls.add_file_date_column:
            return None
        return db.Column(
            UTCDateTime,
            nullable=not cls.file_required,
            default=now_utc
        )

    @property
    def storage(self):
        """The Storage object used to store the file."""
        if self.storage_backend is None:
            raise RuntimeError('No storage backend set')
        return get_storage(self.storage_backend)

    def get_local_path(self):
        """Return context manager that will yield physical path.
           This should be avoided in favour of using the actual file contents"""
        return self.storage.get_local_path(self.storage_file_id)

    def _build_storage_path(self):
        """Should return a tuple containing the name of the storage backend
        to use and the actual path of that will be used to store the resource
        using the former."""
        raise NotImplementedError

    def save(self, data):
        """Saves a file in the file storage.

        This requires the AttachmentFile to be associated with
        an Attachment which needs to be associated with a Folder since
        the data from these objects is needed to generate the path
        used to store the file.

        :param data: bytes or a file-like object
        """
        assert self.storage_backend is None and self.storage_file_id is None and self.size is None
        if self.version_of:
            assert getattr(self, self.version_of) is not None
        self.storage_backend, path = self._build_storage_path()
        self.storage_file_id = self.storage.save(path, self.content_type, self.filename, data)
        self.size = self.storage.getsize(self.storage_file_id)

    def open(self):
        """Returns the stored file as a file-like object"""
        if self.storage_file_id is None:
            raise Exception('There is no file to open')
        return self.storage.open(self.storage_file_id)

    def send(self, inline=True):
        """Sends the file to the user"""
        if self.storage_file_id is None:
            raise Exception('There is no file to send')
        return self.storage.send_file(self.storage_file_id, self.content_type, self.filename, inline=inline)

    def delete(self):
        """Delete the file from storage"""
        if self.storage_file_id is None:
            raise Exception('There is no file to delete')
        self.storage.delete(self.storage_file_id)
        self.storage_backend = None
        self.storage_file_id = None
        self.size = None
        self.content_type = None
        self.filename = None
