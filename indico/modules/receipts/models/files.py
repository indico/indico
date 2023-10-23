# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import JSONB

from indico.core.db import db
from indico.util.fs import secure_filename
from indico.util.locators import locator_property
from indico.util.string import format_repr
from indico.web.flask.util import url_for


class ReceiptFile(db.Model):
    __tablename__ = 'receipt_files'
    __table_args__ = {'schema': 'event_registration'}

    file_id = db.Column(
        db.ForeignKey('indico.files.id'),
        index=True,
        primary_key=True
    )
    registration_id = db.Column(
        db.Integer,
        db.ForeignKey('event_registration.registrations.id'),
        index=True,
        nullable=False
    )
    template_id = db.Column(
        db.ForeignKey('indico.receipt_templates.id'),
        index=True,
        nullable=False
    )
    template_params = db.Column(
        JSONB,
        nullable=False,
        default={}
    )
    is_published = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    file = db.relationship(
        'File',
        lazy=False,
        backref=db.backref(
            'receipt_file',
            cascade='all, delete-orphan',
            lazy=True,
            uselist=False
        )
    )
    registration = db.relationship(
        'Registration',
        lazy=True,
        backref=db.backref(
            'receipt_files',
            primaryjoin='(ReceiptFile.registration_id == Registration.id) & ~ReceiptFile.is_deleted',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    template = db.relationship(
        'ReceiptTemplate',
        lazy=True,
        backref=db.backref(
            'receipt_files',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    def __repr__(self):
        return format_repr(self, 'file_id', 'registration_id', 'template_id')

    @locator_property
    def locator(self):
        return dict(self.registration.locator, file_id=self.file_id,
                    filename=secure_filename(self.file.filename, f'file-{self.file_id}'))

    @property
    def download_url(self):
        return url_for('receipts.download_file', self)
