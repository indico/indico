# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

import posixpath

from sqlalchemy.event import listens_for
from sqlalchemy.ext.associationproxy import association_proxy

from indico.core.config import Config
from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.db.sqlalchemy.protection import ProtectionMixin
from indico.core.storage import get_storage
from indico.modules.attachments.models.principals import AttachmentPrincipal
from indico.modules.attachments.util import can_manage_attachments
from indico.util.contextManager import ContextManager
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import TitledIntEnum
from indico.web.flask.util import url_for


class AttachmentType(TitledIntEnum):
    __titles__ = [None, _('File'), _('Link')]
    file = 1
    link = 2


class Attachment(ProtectionMixin, db.Model):
    __tablename__ = 'attachments'
    __table_args__ = (
        # links: url but no file
        db.CheckConstraint('type != {} OR (link_url IS NOT NULL AND file_id IS NULL)'.format(AttachmentType.link.value),
                           'valid_link'),
        # we can't require the file_id to be NOT NULL for files because of the circular relationship...
        # but we can ensure that we never have both a file_id AND a link_url...for
        db.CheckConstraint('link_url IS NULL OR file_id IS NULL', 'link_or_file'),
        {'schema': 'attachments'}
    )

    #: The ID of the attachment
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the folder the attachment belongs to
    folder_id = db.Column(
        db.Integer,
        db.ForeignKey('attachments.folders.id'),
        nullable=False,
        index=True
    )
    #: The ID of the user who created the attachment
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=False
    )
    #: If the attachment has been deleted
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The name of the attachment
    title = db.Column(
        db.String,
        nullable=False
    )
    #: The description of the attachment
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: The date/time when the attachment was created/modified
    modified_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc,
        onupdate=now_utc
    )
    #: The type of the attachment (file or link)
    type = db.Column(
        PyIntEnum(AttachmentType),
        nullable=False
    )
    #: The target URL for a link attachment
    link_url = db.Column(
        db.String,
        nullable=True
    )
    #: The ID of the latest file for a file attachment
    file_id = db.Column(
        db.Integer,
        db.ForeignKey('attachments.files.id', use_alter=True),
        nullable=True
    )

    #: The user who created the attachment
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'attachments',
            lazy='dynamic'
        )
    )
    #: The list of all files for the attachment
    all_files = db.relationship(
        'AttachmentFile',
        primaryjoin=lambda: Attachment.id == AttachmentFile.attachment_id,
        foreign_keys=lambda: AttachmentFile.attachment_id,
        lazy=True,
        cascade='all, delete-orphan',
        order_by=lambda: AttachmentFile.created_dt.desc(),
        backref=db.backref(
            'attachment',
            lazy=False
        )
    )
    #: The currently active file for the attachment
    file = db.relationship(
        'AttachmentFile',
        primaryjoin=lambda: Attachment.file_id == AttachmentFile.id,
        foreign_keys=file_id,
        lazy=False,
        post_update=True
    )
    #: The folder containing the attachment
    folder = db.relationship(
        'AttachmentFolder',
        lazy=True,
        backref=db.backref(
            'all_attachments',
            lazy=True
        )
    )
    _acl = db.relationship(
        'AttachmentPrincipal',
        backref='attachment',
        cascade='all, delete-orphan',
        collection_class=set
    )
    #: The ACL of the folder (used for ProtectionMode.protected)
    acl = association_proxy('_acl', 'principal', creator=lambda v: AttachmentPrincipal(principal=v))

    @property
    def protection_parent(self):
        return self.folder

    @property
    def locator(self):
        return dict(self.folder.locator, attachment_id=self.id)

    def get_download_url(self, absolute=False):
        """Returns the download url for the attachment.

        During static site generation this returns a local URL for the
        file or the target URL for the link.

        :param absolute: If the returned URL should be absolute.
        """
        if ContextManager.get('offlineMode'):
            return _offline_download_url(self)
        else:
            filename = self.file.filename if self.type == AttachmentType.file else 'go'
            return url_for('attachments.download', self, filename=filename, _external=absolute)

    @property
    def download_url(self):
        """The download url for the attachment"""
        return self.get_download_url()

    @property
    def absolute_download_url(self):
        """The absolte download url for the attachment"""
        return self.get_download_url(absolute=True)

    def can_access(self, user, *args, **kwargs):
        """Checks if the user is allowed to access the attachment.

        This is the case if the user has access to see the attachment
        or if the user can manage attachments for the linked object.
        """
        return (super(Attachment, self).can_access(user, *args, **kwargs) or
                can_manage_attachments(self.folder.linked_object, user))

    @return_ascii
    def __repr__(self):
        return '<Attachment({}, {}, {}{}, {}, {})>'.format(
            self.id,
            self.title,
            self.file if self.type == AttachmentType.file else self.link_url,
            ', is_deleted=True' if self.is_deleted else '',
            self.protection_repr,
            self.folder_id
        )


class AttachmentFile(db.Model):
    __tablename__ = 'files'
    __table_args__ = {'schema': 'attachments'}

    #: The ID of the file
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated attachment
    attachment_id = db.Column(
        db.Integer,
        db.ForeignKey('attachments.attachments.id'),
        nullable=False,
        index=True
    )
    #: The user who uploaded the file
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        nullable=False,
        index=True
    )
    #: The date/time when the file was uploaded
    created_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc
    )
    #: The name of the file
    filename = db.Column(
        db.String,
        nullable=False
    )
    #: The MIME type of the file
    content_type = db.Column(
        db.String,
        nullable=False
    )
    #: The size of the file (in bytes) - assigned automatically when `save()` is called
    size = db.Column(
        db.BigInteger,
        nullable=False
    )
    storage_backend = db.Column(
        db.String,
        nullable=False
    )
    storage_file_id = db.Column(
        db.String,
        nullable=False
    )

    #: The user who uploaded the file
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'attachment_files',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - attachment (Attachment.all_files)

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

    def save(self, data):
        """Saves a file in the file storage.

        This requires the AttachmentFile to be associated with
        an Attachment which needs to be associated with a Folder since
        the data from these objects is needed to generate the path
        used to store the file.

        :param data: bytes or a file-like object
        """
        assert self.storage_backend is None and self.storage_file_id is None and self.size is None
        assert self.attachment is not None
        folder = self.attachment.folder
        assert folder.linked_object is not None
        if folder.link_type == LinkType.category:
            # category/<id>/...
            path_segments = ['category', unicode(folder.category_id)]
        else:
            # event/<id>/event/...
            path_segments = ['event', unicode(folder.event_id), folder.link_type.name]
            if folder.link_type == LinkType.session:
                # event/<id>/session/<session_id>/...
                path_segments.append(unicode(folder.session_id))
            elif folder.link_type == LinkType.contribution:
                # event/<id>/contribution/<contribution_id>/...
                path_segments.append(unicode(folder.contribution_id))
            elif folder.link_type == LinkType.subcontribution:
                # event/<id>/subcontribution/<contribution_id>-<subcontribution_id>/...
                path_segments.append('{}-{}'.format(folder.contribution_id, folder.subcontribution_id))
        self.attachment.assign_id()
        self.assign_id()
        filename = '{}-{}-{}'.format(self.attachment.id, self.id, self.filename)
        path = posixpath.join(*(path_segments + [filename]))
        self.storage_backend = Config.getInstance().getAttachmentStorage()
        self.storage_file_id = self.storage.save(path, self.content_type, self.filename, data)
        self.size = self.storage.getsize(self.storage_file_id)

    def open(self):
        """Returns the stored file as a file-like object"""
        return self.storage.open(self.storage_file_id)

    def send(self):
        """Sends the file to the user"""
        return self.storage.send_file(self.storage_file_id, self.content_type, self.filename)

    @return_ascii
    def __repr__(self):
        return '<AttachmentFile({}, {}, {}, {})>'.format(
            self.id,
            self.attachment_id,
            self.filename,
            self.content_type
        )


@listens_for(Attachment.file, 'set')
def _add_file_to_relationship(target, value, *unused):
    if value is None:
        # we don't allow file<->link conversions so setting it to None is pointless
        # and would just break integrity
        raise ValueError('file cannot be set to None')
    with db.session.no_autoflush:
        target.all_files.append(value)


def _offline_download_url(attachment):
    # Legacy offline download link generation
    from MaKaC import conference

    if attachment.type == AttachmentType.file:
        if isinstance(attachment.folder.linked_object, conference.Conference):
            path = "events/conference"
        elif isinstance(attachment.folder.linked_object, conference.Session):
            path = "agenda/%s-session" % attachment.folder.linked_object.getId()
        elif isinstance(attachment.folder.linked_object, conference.Contribution):
            path = "agenda/%s-contribution" % attachment.folder.linked_object.getId()
        elif isinstance(attachment.folder.linked_object, conference.SubContribution):
            path = "agenda/%s-subcontribution" % attachment.folder.linked_object.getId()
        else:
            return ''
        return posixpath.join("files", path, str(attachment.id) + "-" + attachment.file.filename)
    else:
        return attachment.link_url
