# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import posixpath
from uuid import uuid4

from sqlalchemy.dialects.postgresql import JSONB, UUID
from werkzeug.exceptions import UnprocessableEntity

from indico.core.config import config
from indico.core.db import db
from indico.core.storage import StoredFileMixin
from indico.modules.files import logger
from indico.util.fs import secure_filename
from indico.util.signing import secure_serializer
from indico.util.string import format_repr, strict_str
from indico.web.flask.util import url_for


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
        default=lambda: str(uuid4())
    )
    #: Whether the file has been associated with something.
    #: Unclaimed files may be deleted automatically after a while.
    claimed = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Arbitrary metadata related to the file. Tis may be set at any time,
    #: but code setting it on an already-claimed file should take into account
    #: that it may already contain some data.
    meta = db.Column(
        JSONB,
        nullable=False,
        default={}
    )

    # relationship backrefs:
    # - custom_boa_of (Event.custom_boa)
    # - data_export_of (DataExportRequest.file)
    # - editing_revision_files (EditingRevisionFile.file)
    # - receipt_file (ReceiptFile.file)

    @classmethod
    def create_from_stream(cls, stream, filename, content_type, context):
        f = cls(filename=filename, content_type=content_type)
        f.save(context, stream)
        if not f.size:
            f.delete()
            raise UnprocessableEntity
        db.session.add(f)
        db.session.flush()
        logger.info('File %r created (context: %r)', f, context)
        return f

    def claim(self):
        """Mark the file as claimed by some object it's linked to.

        Once a file is claimed it will not be automatically deleted anymore.
        """
        self.claimed = True

    def _build_storage_path(self):
        path_segments = list(map(strict_str, self.__context))
        self.assign_id()
        filename = '{}-{}'.format(self.id, secure_filename(self.filename, 'file'))
        path = posixpath.join(*path_segments, filename)
        return config.ATTACHMENT_STORAGE, path

    def save(self, context, data):
        self.__context = context
        super().save(data)
        del self.__context

    @property
    def signed_download_url(self):
        return url_for('files.download_file', uuid=self.uuid,
                       token=secure_serializer.dumps(self.uuid.hex, salt='file-download'), _external=True)

    def as_attachment(self):
        """Return the file as an attachment in the format expected by the util `make_email`."""
        with self.open() as f:
            return secure_filename(self.filename, 'file'), f.read(), self.content_type

    def __repr__(self):
        return format_repr(self, 'id', 'uuid', 'content_type', _text=self.filename)
