# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import posixpath

from flask import g
from sqlalchemy.ext.associationproxy import association_proxy

from indico.core.config import config
from indico.core.db import db
from indico.core.db.sqlalchemy import PyIntEnum, UTCDateTime
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.db.sqlalchemy.protection import ProtectionMixin
from indico.core.db.sqlalchemy.util.session import no_autoflush
from indico.core.storage import StoredFileMixin, VersionedResourceMixin
from indico.modules.attachments.models.principals import AttachmentPrincipal
from indico.modules.attachments.preview import get_file_previewer
from indico.modules.attachments.util import can_manage_attachments
from indico.util.date_time import now_utc
from indico.util.fs import secure_filename
from indico.util.i18n import _
from indico.util.string import return_ascii, strict_unicode
from indico.util.struct.enum import RichIntEnum
from indico.web.flask.util import url_for


class AttachmentType(RichIntEnum):
    __titles__ = [None, _('File'), _('Link')]
    file = 1
    link = 2


class AttachmentFile(StoredFileMixin, db.Model):
    __tablename__ = 'files'
    __table_args__ = {'schema': 'attachments'}

    version_of = 'attachment'

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
    def is_previewable(self):
        return get_file_previewer(self) is not None

    @no_autoflush
    def _build_storage_path(self):
        folder = self.attachment.folder
        assert folder.object is not None
        if folder.link_type == LinkType.category:
            # category/<id>/...
            path_segments = ['category', strict_unicode(folder.category.id)]
        else:
            # event/<id>/event/...
            path_segments = ['event', strict_unicode(folder.event.id), folder.link_type.name]
            if folder.link_type == LinkType.session:
                # event/<id>/session/<session_id>/...
                path_segments.append(strict_unicode(folder.session.id))
            elif folder.link_type == LinkType.contribution:
                # event/<id>/contribution/<contribution_id>/...
                path_segments.append(strict_unicode(folder.contribution.id))
            elif folder.link_type == LinkType.subcontribution:
                # event/<id>/subcontribution/<subcontribution_id>/...
                path_segments.append(strict_unicode(folder.subcontribution.id))
        self.attachment.assign_id()
        self.assign_id()
        filename = '{}-{}-{}'.format(self.attachment.id, self.id, secure_filename(self.filename, 'file'))
        path = posixpath.join(*(path_segments + [filename]))
        return config.ATTACHMENT_STORAGE, path

    @return_ascii
    def __repr__(self):
        return '<AttachmentFile({}, {}, {}, {})>'.format(
            self.id,
            self.attachment_id,
            self.filename,
            self.content_type
        )


class Attachment(ProtectionMixin, VersionedResourceMixin, db.Model):
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

    stored_file_table = 'attachments.files'
    stored_file_class = AttachmentFile
    stored_file_fkey = 'attachment_id'

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

    #: The user who created the attachment
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'attachments',
            lazy='dynamic'
        )
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
    acl_entries = db.relationship(
        'AttachmentPrincipal',
        backref='attachment',
        cascade='all, delete-orphan',
        collection_class=set
    )
    #: The ACL of the folder (used for ProtectionMode.protected)
    acl = association_proxy('acl_entries', 'principal', creator=lambda v: AttachmentPrincipal(principal=v))

    # relationship backrefs:
    # - legacy_mapping (LegacyAttachmentMapping.attachment)

    @property
    def protection_parent(self):
        return self.folder

    @property
    def locator(self):
        return dict(self.folder.locator, attachment_id=self.id)

    def get_download_url(self, absolute=False):
        """Return the download url for the attachment.

        During static site generation this returns a local URL for the
        file or the target URL for the link.

        :param absolute: If the returned URL should be absolute.
        """
        if g.get('static_site'):
            return _offline_download_url(self)
        else:
            filename = self.file.filename if self.type == AttachmentType.file else 'go'
            return url_for('attachments.download', self, filename=filename, _external=absolute)

    @property
    def download_url(self):
        """The download url for the attachment."""
        return self.get_download_url()

    @property
    def absolute_download_url(self):
        """The absolute download url for the attachment."""
        return self.get_download_url(absolute=True)

    def can_access(self, user, *args, **kwargs):
        """Check if the user is allowed to access the attachment.

        This is the case if the user has access to see the attachment
        or if the user can manage attachments for the linked object.
        """
        return (super(Attachment, self).can_access(user, *args, **kwargs) or
                can_manage_attachments(self.folder.object, user))

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


# Register all SQLAlchemy-related events
Attachment.register_versioned_resource_events()
Attachment.register_protection_events()


def _offline_download_url(attachment):
    # Legacy offline download link generation
    if attachment.type == AttachmentType.file:
        if isinstance(attachment.folder.object, db.m.Event):
            path = ""
        elif isinstance(attachment.folder.object, db.m.Session):
            path = "{}-session".format(attachment.folder.session.friendly_id)
        elif isinstance(attachment.folder.object, db.m.Contribution):
            path = "{}-contribution".format(attachment.folder.contribution.friendly_id)
        elif isinstance(attachment.folder.object, db.m.SubContribution):
            path = "{}-subcontribution".format(attachment.folder.subcontribution.friendly_id)
        else:
            return ''
        return posixpath.join("material", path, str(attachment.id) + "-" + attachment.file.filename)
    else:
        return attachment.link_url
