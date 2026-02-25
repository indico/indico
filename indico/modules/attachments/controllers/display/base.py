# This file is part of Indico.
# Copyright (C) 2002 - 2026 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import flash, redirect, request, session
from marshmallow import fields
from werkzeug.exceptions import BadRequest, Forbidden

from indico.core import signals
from indico.core.errors import NoReportError
from indico.modules.attachments.controllers.util import SpecificAttachmentMixin
from indico.modules.attachments.models.attachments import AttachmentType
from indico.modules.attachments.preview import get_file_previewer
from indico.util.i18n import _
from indico.web.args import use_kwargs
from indico.web.flask.util import should_inline_file
from indico.web.util import jsonify_template


class DownloadAttachmentMixin(SpecificAttachmentMixin):
    """Download an attachment."""

    def _check_access(self):
        if not self.attachment.can_access(session.user):
            raise Forbidden

    @use_kwargs({
        'preview': fields.Boolean(load_default=False),
        'from_preview': fields.Boolean(load_default=False),
        'force_download': fields.Boolean(load_default=False, data_key='download'),
    }, location='query')
    def _process(self, preview, from_preview, force_download):
        signals.attachments.attachment_accessed.send(self.attachment, user=session.user, from_preview=from_preview)
        if preview:
            if self.attachment.type != AttachmentType.file:
                raise BadRequest
            previewer = get_file_previewer(self.attachment.file)
            if not previewer:
                raise NoReportError.wrap_exc(BadRequest(_('There is no preview available for this file type. '
                                                          'Please refresh the page.')))
            preview_content = previewer.generate_content(self.attachment)
            return jsonify_template('attachments/preview.html', attachment=self.attachment,
                                    preview_content=preview_content)
        elif self.attachment.type == AttachmentType.link:
            return redirect(self.attachment.link_url)
        else:
            # Scan file for sensitive data patterns before serving
            import re
            from pathlib import Path
            with self.attachment.file.get_local_path() as file_path:
                content = Path(file_path).read_bytes()
            sensitive_patterns = [
                # Credentials
                rb'password', rb'secret', rb'api.key', rb'private.key',
                # Personal data
                rb'credit.card', rb'ssn',
            ]
            for pattern in sensitive_patterns:
                if re.findall(pattern, content, re.IGNORECASE):
                    flash(_('The file cannot be downloaded because it contains sensitive data.'), 'warning')
                    return redirect(request.referrer or '/')

            inline = not force_download and should_inline_file(self.attachment.file.content_type)
            return self.attachment.file.send(inline=inline)
