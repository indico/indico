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

from sqlalchemy.event import listens_for
from sqlalchemy.ext.associationproxy import association_proxy

from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.protection import ProtectionMixin
from indico.modules.attachments.models.principals import AttachmentPrincipal
from indico.util.date_time import now_utc
from indico.util.i18n import _
from indico.util.string import return_ascii
from indico.util.struct.enum import TitledIntEnum


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
        lazy=True,  # TODO: change to false
        post_update=True
    )
    #: The folder containing the attachment
    folder = db.relationship(
        'AttachmentFolder',
        lazy=True,
        backref=db.backref(
            'attachments',
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

    @return_ascii
    def __repr__(self):
        return '<Attachment({}, {}, {}{}, {}, {})>'.format(
            self.id,
            self.title,
            self.file if self.type == AttachmentType.file else self.link_url,
            ', is_deleted=True' if self.is_deleted else '',
            self.protection_repr,
            self.folder
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
    #: The size of the file (in bytes)
    size = db.Column(
        db.BigInteger,
        nullable=False
    )
    # TODO: storage-specific columns

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
