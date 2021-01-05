# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.attachments.models.attachments import Attachment, AttachmentType
from indico.modules.events.api import EventBaseHook
from indico.web.http_api.hooks.base import HTTPAPIHook
from indico.web.http_api.metadata.serializer import Serializer
from indico.web.http_api.responses import HTTPAPIError


@HTTPAPIHook.register
class FileHook(EventBaseHook):
    """
    Example: /export/event/1/session/2/contrib/3/subcontrib/4/material/Slides/5.bin
    """
    TYPES = ('file',)
    METHOD_NAME = 'export_file'
    DEFAULT_DETAIL = 'bin'
    VALID_FORMATS = ('bin',)
    GUEST_ALLOWED = True
    RE = (r'(?P<event>[\w\s]+)(/session/(?P<session>[\w\s]+))?'
          r'(/contrib/(?P<contrib>[\w\s]+))?(/subcontrib/(?P<subcontrib>[\w\s]+))?'
          r'/material/(?P<material>[^/]+)/(?P<res>\d+)')
    NO_CACHE = True

    def _getParams(self):
        super(FileHook, self)._getParams()

        self._attachment = Attachment.get(int(self._pathParams['res']))

        if not self._attachment:
            raise HTTPAPIError("File not found", 404)

    def export_file(self, user):
        if self._attachment.type != AttachmentType.file:
            raise HTTPAPIError("Resource is not a file", 404)

        return self._attachment.file.send()

    def _has_access(self, user):
        return self._attachment.can_access(user)


class FileSerializer(Serializer):

    encapsulate = False
    schemaless = False

    def _execute(self, fdata):
        return fdata

    def get_response_content_type(self):
        # we already have a response with the correct headers
        return None


Serializer.register('bin', FileSerializer)
