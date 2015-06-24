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

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.links import LinkMixin
from indico.core.db.sqlalchemy.protection import ProtectionMixin, ProtectionMode
from indico.core.db.sqlalchemy.util.models import auto_table_args
from indico.modules.attachments.models.principals import AttachmentFolderPrincipal
from indico.util.decorators import strict_classproperty
from indico.util.string import return_ascii


class AttachmentFolder(LinkMixin, ProtectionMixin, db.Model):
    __tablename__ = 'folders'
    unique_links = 'is_default'

    @strict_classproperty
    @staticmethod
    def __auto_table_args():
        default_inheriting = 'not (is_default and protection_mode != {})'.format(ProtectionMode.inheriting.value)
        return (db.CheckConstraint(default_inheriting, 'default_inheriting'),
                db.CheckConstraint('is_default = (title IS NULL)', 'default_or_title'),
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

    _acl = db.relationship(
        'AttachmentFolderPrincipal',
        backref='folder',
        cascade='all, delete-orphan',
        collection_class=set
    )
    #: The ACL of the folder (used for ProtectionMode.protected)
    acl = association_proxy('_acl', 'principal', creator=lambda v: AttachmentFolderPrincipal(principal=v))

    # relationship backrefs:
    # - attachments (Attachment.folder)

    @return_ascii
    def __repr__(self):
        return '<AttachmentFolder({}, {}{}{}, {}, {})>'.format(
            self.id,
            self.title,
            ', is_default=True' if self.is_default else '',
            ', is_deleted=True' if self.is_deleted else '',
            self.protection_repr,
            self.link_repr
        )
