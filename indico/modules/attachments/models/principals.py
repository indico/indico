# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.core.db.sqlalchemy.principals import PrincipalMixin
from indico.core.db.sqlalchemy.util.models import auto_table_args


class AttachmentFolderPrincipal(PrincipalMixin, db.Model):
    __tablename__ = 'folder_principals'
    principal_backref_name = 'in_attachment_folder_acls'
    unique_columns = ('folder_id',)
    allow_event_roles = True
    allow_category_roles = True
    allow_registration_forms = True

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='attachments')

    #: The ID of the acl entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated folder
    folder_id = db.Column(
        db.Integer,
        db.ForeignKey('attachments.folders.id'),
        nullable=False
    )

    # relationship backrefs:
    # - folder (AttachmentFolder.acl_entries)

    def __repr__(self):
        return f'<AttachmentFolderPrincipal({self.id}, {self.folder_id}, {self.principal})>'


class AttachmentPrincipal(PrincipalMixin, db.Model):
    __tablename__ = 'attachment_principals'
    principal_backref_name = 'in_attachment_acls'
    unique_columns = ('attachment_id',)
    allow_event_roles = True
    allow_category_roles = True
    allow_registration_forms = True

    @declared_attr
    def __table_args__(cls):
        return auto_table_args(cls, schema='attachments')

    #: The ID of the acl entry
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the associated attachment
    attachment_id = db.Column(
        db.Integer,
        db.ForeignKey('attachments.attachments.id'),
        nullable=False
    )

    # relationship backrefs:
    # - attachment (Attachment.acl_entries)

    def __repr__(self):
        return f'<AttachmentPrincipal({self.id}, {self.attachment_id}, {self.principal})>'
