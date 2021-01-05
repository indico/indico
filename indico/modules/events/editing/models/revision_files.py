# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.util.fs import secure_filename
from indico.util.locators import locator_property
from indico.util.string import format_repr, return_ascii
from indico.web.flask.util import url_for


class EditingRevisionFile(db.Model):
    __tablename__ = 'revision_files'
    __table_args__ = {'schema': 'event_editing'}

    revision_id = db.Column(
        db.ForeignKey('event_editing.revisions.id'),
        index=True,
        primary_key=True
    )
    file_id = db.Column(
        db.ForeignKey('indico.files.id'),
        index=True,
        primary_key=True
    )
    file_type_id = db.Column(
        db.ForeignKey('event_editing.file_types.id'),
        index=True
    )

    file = db.relationship(
        'File',
        lazy=False,
        backref=db.backref(
            'editing_revision_files',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    file_type = db.relationship(
        'EditingFileType',
        lazy=False,
        backref=db.backref(
            'files',
            cascade='all, delete-orphan',
            lazy=True
        )
    )
    revision = db.relationship(
        'EditingRevision',
        lazy=True,
        backref=db.backref(
            'files',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'revision_id', 'file_id')

    @locator_property
    def locator(self):
        return dict(self.revision.locator, file_id=self.file_id,
                    filename=secure_filename(self.file.filename, 'file-{}'.format(self.file_id)))

    @property
    def download_url(self):
        return url_for('event_editing.download_file', self)

    @property
    def external_download_url(self):
        return url_for('event_editing.download_file', self, _external=True)
