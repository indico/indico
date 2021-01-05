# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import posixpath

from indico.core.config import config
from indico.core.db import db
from indico.core.storage import StoredFileMixin
from indico.util.fs import secure_filename
from indico.util.string import format_repr, return_ascii, strict_unicode, text_to_repr


class AbstractFile(StoredFileMixin, db.Model):
    __tablename__ = 'files'
    __table_args__ = {'schema': 'event_abstracts'}

    # StoredFileMixin settings
    add_file_date_column = False

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    abstract_id = db.Column(
        db.Integer,
        db.ForeignKey('event_abstracts.abstracts.id'),
        nullable=False,
        index=True
    )
    abstract = db.relationship(
        'Abstract',
        lazy=True,
        backref=db.backref(
            'files',
            lazy=True,
            cascade='all, delete-orphan'
        )
    )

    @property
    def locator(self):
        return dict(self.abstract.locator, file_id=self.id, filename=self.filename)

    def _build_storage_path(self):
        self.abstract.assign_id()
        path_segments = ['event', strict_unicode(self.abstract.event.id),
                         'abstracts', strict_unicode(self.abstract.id)]
        self.assign_id()
        filename = '{}-{}'.format(self.id, secure_filename(self.filename, 'file'))
        path = posixpath.join(*(path_segments + [filename]))
        return config.ATTACHMENT_STORAGE, path

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'abstract_id', content_type=None, _text=text_to_repr(self.filename))
