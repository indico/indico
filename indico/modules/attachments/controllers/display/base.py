# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from flask import redirect, session
from werkzeug.exceptions import Forbidden

from indico.modules.attachments.models.attachments import AttachmentType
from indico.modules.attachments.controllers.util import SpecificAttachmentMixin


class DownloadAttachmentMixin(SpecificAttachmentMixin):
    """Download an attachment"""

    def _checkProtection(self):
        if not self.attachment.can_access(session.user):
            raise Forbidden

    def _process(self):
        # TODO: trigger an 'attachment downloaded' signal
        if self.attachment.type == AttachmentType.link:
            return redirect(self.attachment.link_url)
        else:
            return self.attachment.file.send()
