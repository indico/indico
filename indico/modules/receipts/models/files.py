# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
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
        db.ForeignKey('event_registration.registrations.id', ondelete='CASCADE'),
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
            passive_deletes=True,
            lazy=True
        )
    )
    template = db.relationship(
        'ReceiptTemplate',
        lazy=True,
        backref=db.backref(
            'receipt_files',
            lazy=True
        )
    )

    def __repr__(self):
        return format_repr(self, 'file_id', 'registration_id', 'template_id', is_deleted=False)

    @locator_property
    def locator(self):
        return {**self.registration.locator, 'file_id': self.file_id}

    @locator.filename
    def locator(self):
        return {**self.locator, 'filename': secure_filename(self.file.filename, f'file-{self.file_id}.pdf')}

    @locator.registrant
    def locator(self):
        return {
            **self.registration.locator.registrant,
            'file_id': self.file_id,
            'filename': secure_filename(self.file.filename, f'file-{self.file_id}.pdf'),
        }

    @property
    def registrant_download_url(self):
        return url_for('event_registration.receipt_download_display', self.locator.registrant)

    @property
    def external_registrant_download_url(self):
        return url_for('event_registration.receipt_download_display', self.locator.registrant, _external=True)
