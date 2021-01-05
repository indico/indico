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
from indico.util.string import return_ascii, strict_unicode


class ImageFile(StoredFileMixin, db.Model):
    __tablename__ = 'image_files'
    __table_args__ = {'schema': 'events'}

    # Image files are not version-controlled
    version_of = None

    #: The ID of the file
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    #: The event the image belongs to
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('events.events.id'),
        nullable=False,
        index=True
    )

    event = db.relationship(
        'Event',
        lazy=False,
        backref=db.backref(
            'layout_images',
            lazy='dynamic'
        )
    )

    # relationship backrefs:
    # - legacy_mapping (LegacyImageMapping.image)

    @property
    def locator(self):
        return dict(self.event.locator, image_id=self.id, filename=self.filename)

    def _build_storage_path(self):
        path_segments = ['event', strict_unicode(self.event.id), 'images']
        self.assign_id()
        filename = '{}-{}'.format(self.id, secure_filename(self.filename, 'file'))
        path = posixpath.join(*(path_segments + [filename]))
        return config.ATTACHMENT_STORAGE, path

    @return_ascii
    def __repr__(self):
        return '<ImageFile({}, {}, {}, {})>'.format(
            self.id,
            self.event_id,
            self.filename,
            self.content_type
        )
