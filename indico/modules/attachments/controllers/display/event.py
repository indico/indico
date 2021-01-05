# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import redirect, request, session
from werkzeug.exceptions import Forbidden

from indico.modules.attachments.controllers.display.base import DownloadAttachmentMixin
from indico.modules.attachments.controllers.event_package import AttachmentPackageMixin
from indico.modules.attachments.controllers.util import SpecificFolderMixin
from indico.modules.attachments.views import (WPEventFolderDisplay, WPPackageEventAttachmentsDisplay,
                                              WPPackageEventAttachmentsDisplayConference)
from indico.modules.events.controllers.base import RHDisplayEventBase
from indico.modules.events.models.events import EventType


class RHDownloadEventAttachment(DownloadAttachmentMixin, RHDisplayEventBase):
    def _process_args(self):
        RHDisplayEventBase._process_args(self)
        DownloadAttachmentMixin._process_args(self)

    def _check_access(self):
        try:
            DownloadAttachmentMixin._check_access(self)
        except Forbidden:
            # if we get here the user has no access to the attachment itself so we
            # trigger the event access check since it may show the access key form
            # or registration required message
            RHDisplayEventBase._check_access(self)
            # the user may have access to the event but not the material so if we
            # are here we need to re-raise the original exception
            raise


class RHListEventAttachmentFolder(SpecificFolderMixin, RHDisplayEventBase):
    def _process_args(self):
        RHDisplayEventBase._process_args(self)
        SpecificFolderMixin._process_args(self)

    def _check_access(self):
        if not self.folder.can_access(session.user):
            # basically the same logic as in RHDownloadEventAttachment. see the comments
            # there for a more detailed explanation.
            RHDisplayEventBase._check_access(self)
            raise Forbidden

    def _process(self):
        if request.args.get('redirect_if_single') == '1' and len(self.folder.attachments) == 1:
            return redirect(self.folder.attachments[0].download_url)

        return WPEventFolderDisplay.render_template('folder.html', self.event, folder=self.folder)


class RHPackageEventAttachmentsDisplay(AttachmentPackageMixin, RHDisplayEventBase):
    @property
    def wp(self):
        if self.event.type_ == EventType.conference:
            return WPPackageEventAttachmentsDisplayConference
        else:
            return WPPackageEventAttachmentsDisplay
