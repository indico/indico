# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events.management.views import WPEventManagement
from indico.modules.events.views import WPConferenceDisplayBase, WPSimpleEventDisplayBase
from indico.web.views import WPJinjaMixin


class AttachmentsMixin(WPJinjaMixin):
    template_prefix = 'attachments/'
    base_wp = None

    def _get_page_content(self, params):
        return WPJinjaMixin._get_page_content(self, params)


class WPEventAttachments(AttachmentsMixin, WPEventManagement):
    base_wp = WPEventManagement
    sidemenu_option = 'attachments'
    ALLOW_JSON = True


class WPEventFolderDisplay(WPSimpleEventDisplayBase, WPJinjaMixin):
    template_prefix = 'attachments/'

    def _get_body(self, params):
        return WPJinjaMixin._get_page_content(self, params)


class WPPackageEventAttachmentsManagement(WPEventAttachments, WPJinjaMixin):
    template_prefix = 'attachments/'


class WPPackageEventAttachmentsDisplayConference(WPConferenceDisplayBase):
    template_prefix = 'attachments/'


class WPPackageEventAttachmentsDisplay(WPSimpleEventDisplayBase, WPJinjaMixin):
    template_prefix = 'attachments/'

    def _get_body(self, params):
        return WPJinjaMixin._get_page_content(self, params)
