# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

# indico imports
from indico.web.http_api.metadata.serializer import Serializer

from indico.modules.attachments.models.attachments import Attachment, AttachmentType
from indico.modules.events.api import EventBaseHook
from indico.web.http_api.hooks.base import HTTPAPIHook
from indico.web.http_api.responses import HTTPAPIError


@HTTPAPIHook.register
class FileHook(EventBaseHook):
    """
    Example: /export/event/1/session/2/contrib/3/subcontrib/4/material/Slides/5.bin?ak=00000000-0000-0000-0000-000000000000
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

    def export_file(self, aw):
        if self._attachment.type != AttachmentType.file:
            raise HTTPAPIError("Resource is not a file", 404)

        return self._attachment.file.send()

    def _hasAccess(self, aw):
        avatar = aw.getUser()
        user = avatar.user if avatar else None
        return self._attachment.can_access(user)


class FileSerializer(Serializer):

    encapsulate = False
    schemaless = False

    def _execute(self, fdata):
        return fdata

    def set_headers(self, response):
        # Usually the serializer would set the mime type on the ResponseUtil. however, this would trigger
        # the fail-safe that prevents us from returning a response_class while setting custom headers.
        # Besides that we don't need it since the send_file response already has the correct mime type.
        pass


Serializer.register('bin', FileSerializer)
