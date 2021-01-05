# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from collections import defaultdict

from flask import g
from sqlalchemy.event import listens_for
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkMixin, LinkType
from indico.core.db.sqlalchemy.protection import ProtectionMixin, ProtectionMode
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.modules.attachments.models.attachments import Attachment
from indico.modules.attachments.models.principals import AttachmentFolderPrincipal
from indico.modules.attachments.util import can_manage_attachments
from indico.util.decorators import strict_classproperty
from indico.util.locators import locator_property
from indico.util.string import return_ascii


class AttachmentFolder(LinkMixin, ProtectionMixin, db.Model):
    __tablename__ = 'folders'
    allowed_link_types = LinkMixin.allowed_link_types - {LinkType.session_block}
    unique_links = 'is_default'
    events_backref_name = 'all_attachment_folders'
    link_backref_name = 'attachment_folders'
    link_backref_lazy = 'dynamic'

    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        default_inheriting = 'not (is_default and protection_mode != {})'.format(ProtectionMode.inheriting.value)
        return (db.CheckConstraint(default_inheriting, 'default_inheriting'),
                db.CheckConstraint('is_default = (title IS NULL)', 'default_or_title'),
                db.CheckConstraint('not (is_default and is_deleted)', 'default_not_deleted'),
                db.CheckConstraint('not (is_hidden and is_always_visible)', 'is_hidden_not_is_always_visible'),
                {'schema': 'attachments'})

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls)

    #: The ID of the folder
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The name of the folder (``None`` for the default folder)
    title = db.Column(
        db.String,
        nullable=True
    )
    #: The description of the folder
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: If the folder has been deleted
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: If the folder is the default folder (used for "folder-less" files)
    is_default = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: If the folder is always visible (even if you cannot access it)
    is_always_visible = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: If the folder is never shown in the frontend (even if you can access it)
    is_hidden = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    acl_entries = db.relationship(
        'AttachmentFolderPrincipal',
        backref='folder',
        cascade='all, delete-orphan',
        collection_class=set
    )
    #: The ACL of the folder (used for ProtectionMode.protected)
    acl = association_proxy('acl_entries', 'principal', creator=lambda v: AttachmentFolderPrincipal(principal=v))

    #: The list of attachments that are not deleted, ordered by name
    attachments = db.relationship(
        'Attachment',
        primaryjoin=lambda: (Attachment.folder_id == AttachmentFolder.id) & ~Attachment.is_deleted,
        order_by=lambda: db.func.lower(Attachment.title),
        viewonly=True,
        lazy=True
    )

    # relationship backrefs:
    # - all_attachments (Attachment.folder)
    # - legacy_mapping (LegacyAttachmentFolderMapping.folder)

    @property
    def protection_parent(self):
        return self.object

    @classmethod
    def get_or_create_default(cls, linked_object):
        """Get the default folder for the given object or creates it."""
        folder = cls.find_first(is_default=True, object=linked_object)
        if folder is None:
            folder = cls(is_default=True, object=linked_object)
        return folder

    @classmethod
    def get_or_create(cls, linked_object, title=None):
        """Get a folder for the given object or create it.

        If no folder title is specified, the default folder will be
        used.  It is the caller's responsibility to add the folder
        or an object (such as an attachment) associated with it
        to the SQLAlchemy session using ``db.session.add(...)``.
        """
        if title is None:
            return AttachmentFolder.get_or_create_default(linked_object)
        else:
            folder = AttachmentFolder.find_first(object=linked_object, is_default=False, is_deleted=False, title=title)
            return folder or AttachmentFolder(object=linked_object, title=title)

    @locator_property
    def locator(self):
        return dict(self.object.locator, folder_id=self.id)

    def can_access(self, user, *args, **kwargs):
        """Check if the user is allowed to access the folder.

        This is the case if the user has access the folder or if the
        user can manage attachments for the linked object.
        """
        return (super(AttachmentFolder, self).can_access(user, *args, **kwargs) or
                can_manage_attachments(self.object, user))

    def can_view(self, user):
        """Check if the user can see the folder.

        This does not mean the user can actually access its contents.
        It just determines if it is visible to him or not.
        """
        if self.is_hidden:
            return False
        if not self.object.can_access(user):
            return False
        return self.is_always_visible or super(AttachmentFolder, self).can_access(user)

    @classmethod
    def get_for_linked_object(cls, linked_object, preload_event=False):
        """Get the attachments for the given object.

        This only returns attachments that haven't been deleted.

        :param linked_object: A category, event, session, contribution or
                              subcontribution.
        :param preload_event: If all attachments for the same event should
                              be pre-loaded and cached in the app context.
                              This must not be used when ``linked_object``
                              is a category.
        """
        from indico.modules.attachments.api.util import get_event

        event = get_event(linked_object)

        if event and event in g.get('event_attachments', {}):
            return g.event_attachments[event].get(linked_object, [])
        elif not preload_event or not event:
            return (linked_object.attachment_folders.filter_by(is_deleted=False)
                    .order_by(AttachmentFolder.is_default.desc(), db.func.lower(AttachmentFolder.title))
                    .options(joinedload(AttachmentFolder.attachments))
                    .all())
        else:
            if 'event_attachments' not in g:
                g.event_attachments = {}
            g.event_attachments[event] = defaultdict(list)
            query = (event.all_attachment_folders
                     .filter_by(is_deleted=False)
                     .order_by(AttachmentFolder.is_default.desc(), db.func.lower(AttachmentFolder.title))
                     .options(joinedload(AttachmentFolder.attachments),
                              joinedload(AttachmentFolder.linked_event),
                              joinedload(AttachmentFolder.session),
                              joinedload(AttachmentFolder.contribution),
                              joinedload(AttachmentFolder.subcontribution)))

            # populate cache
            for obj in query:
                g.event_attachments[event][obj.object].append(obj)

            return g.event_attachments[event].get(linked_object, [])

    @return_ascii
    def __repr__(self):
        return '<AttachmentFolder({}, {}{}{}{}, {}, {})>'.format(
            self.id,
            self.title,
            ', is_default=True' if self.is_default else '',
            ', is_always_visible=False' if not self.is_always_visible else '',
            ', is_hidden=True' if self.is_hidden else '',
            ', is_deleted=True' if self.is_deleted else '',
            self.protection_repr
        )


@listens_for(AttachmentFolder.attachments, 'append')
@listens_for(AttachmentFolder.attachments, 'remove')
def _wrong_attachments_modified(target, value, *unused):
    raise Exception('AttachmentFolder.attachments is view-only. Use all_attachments for write operations!')


AttachmentFolder.register_link_events()
AttachmentFolder.register_protection_events()
