# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.core.db import db
from indico.util.string import format_repr, return_ascii


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
