# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import mimetypes

from flask import request
from marshmallow import fields
from werkzeug.exceptions import Forbidden

from indico.core.db import db
from indico.modules.files import logger
from indico.modules.files.models.files import File
from indico.modules.files.schemas import FileSchema
from indico.web.args import use_kwargs
from indico.web.rh import RHProtected


class UploadFileMixin(object):
    """Mixin for RHs using the generic file upload system.

    An RH using this mixin needs to override the ``get_file_context`` method
    to specify how the file gets stored.
    """

    @use_kwargs({
        'file': fields.Field(location='files', required=True)
    })
    def _process(self, file):
        context = self.get_file_context()
        content_type = mimetypes.guess_type(file.filename)[0] or file.mimetype or 'application/octet-stream'
        f = File(filename=file.filename, content_type=content_type)
        f.save(context, file.stream)
        db.session.add(f)
        db.session.flush()
        logger.info('File %r uploaded (context: %r)', f, context)
        return FileSchema().jsonify(f), 201

    def get_file_context(self):
        """The context of where the file is being uploaded.

        :return: A tuple/list of path segments to use when storing the file.

        For example, if a file is being uploaded to an event, you'd
        return ``['event', EVENTID]`` so the file gets stored under
        ``event/EVENTID/...`` in the storage backend.
        """
        raise NotImplementedError


class RHFileBase(RHProtected):
    def _process_args(self):
        self.file = File.query.filter_by(uuid=request.view_args['uuid']).first_or_404()


class RHDeleteFile(RHFileBase):
    def _check_access(self):
        if self.file.claimed:
            raise Forbidden('Cannot delete claimed file')

    def _process(self):
        self.file.delete()
        logger.info('File %r deleted', self.file)
        db.session.delete(self.file)
        return '', 204


class RHFileInfo(RHFileBase):
    def _process(self):
        return FileSchema().jsonify(self.file)
