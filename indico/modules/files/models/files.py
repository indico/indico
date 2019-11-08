# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import posixpath
from uuid import uuid4

from sqlalchemy.dialects.postgresql import JSONB, UUID

from indico.core.config import config
from indico.core.db import db
from indico.core.storage import StoredFileMixin
from indico.util.fs import secure_filename
from indico.util.string import format_repr, return_ascii, strict_unicode


class File(StoredFileMixin, db.Model):
    __tablename__ = 'files'
    __table_args__ = {'schema': 'indico'}

    id = db.Column(
        db.Integer,
        primary_key=True
    )
    uuid = db.Column(
        UUID(as_uuid=True),
        index=True,
        unique=True,
        nullable=False,
        default=lambda: unicode(uuid4())
    )
    #: Whether the file has been associated with something.
    #: Unclaimed files may be deleted automatically after a while.
    claimed = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Metadata that may be set when the file gets claimed.
    meta = db.Column(
        JSONB,
        nullable=False,
        default={}
    )

    def claim(self, **meta):
        """Mark the file as claimed by some object it's linked to.

        By claiming a file the linked object takes ownership of it so the
        file will not be automatically deleted.

        :param force: Whether the file can already
        """
        self.claimed = True
        # XXX: Should we check for conflicts with existing metadata in case the
        # file was already claimed?
        self.meta = meta

    def _build_storage_path(self):
        path_segments = list(map(strict_unicode, self.__context))
        self.assign_id()
        filename = '{}-{}'.format(self.id, secure_filename(self.filename, 'file'))
        path = posixpath.join(*(path_segments + [filename]))
        return config.ATTACHMENT_STORAGE, path

    def save(self, context, data):
        self.__context = context
        super(File, self).save(data)
        del self.__context

    @return_ascii
    def __repr__(self):
        return format_repr(self, 'id', 'uuid', 'content_type', _text=self.filename)
