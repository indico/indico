# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import posixpath

from indico.core.config import config
from indico.core.db import db
from indico.core.storage import StoredFileMixin
from indico.util.string import strict_str
from indico.web.flask.util import url_for


class DesignerImageFile(StoredFileMixin, db.Model):
    __tablename__ = 'designer_image_files'
    __table_args__ = {'schema': 'indico'}

    # Image files are not version-controlled
    version_of = None

    #: The ID of the file
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The designer template the image belongs to
    template_id = db.Column(
        db.Integer,
        db.ForeignKey('indico.designer_templates.id'),
        nullable=False,
        index=True
    )

    template = db.relationship(
        'DesignerTemplate',
        lazy=False,
        foreign_keys=template_id,
        backref=db.backref(
            'images',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    @property
    def download_url(self):
        return url_for('designer.download_image', self)

    @property
    def locator(self):
        return dict(self.template.locator, image_id=self.id, filename=self.filename)

    def _build_storage_path(self):
        path_segments = ['designer_templates', strict_str(self.template.id), 'images']
        self.assign_id()
        filename = f'{self.id}-{self.filename}'
        path = posixpath.join(*path_segments, filename)
        return config.ATTACHMENT_STORAGE, path

    def __repr__(self):
        return f'<DesignerImageFile({self.id}, {self.template_id}, {self.filename}, {self.content_type})>'
