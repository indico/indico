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

from MaKaC.webinterface.meeting import WPMeetingDisplay
from MaKaC.webinterface.pages.base import WPJinjaMixin
from MaKaC.webinterface.pages.category import WPCategoryModifBase
from MaKaC.webinterface.pages.conferences import (WPConferenceModifBase, WPConfModifToolsBase,
                                                  WPConferenceDefaultDisplayBase)
from MaKaC.webinterface.pages.sessions import WPSessionModifBase
from MaKaC.webinterface.pages.contributions import WPContributionModifBase
from MaKaC.webinterface.pages.subContributions import WPSubContributionModifBase


class AttachmentsMixin(WPJinjaMixin):
    template_prefix = 'attachments/'
    base_wp = None

    def _getPageContent(self, params):
        return WPJinjaMixin._getPageContent(self, params)


class EventObjectAttachmentsMixin(AttachmentsMixin):
    def _getPageContent(self, params):
        return self.base_wp._getPageContent(self, params)

    def _getTabContent(self, params):
        return AttachmentsMixin._getPageContent(self, params)

    def _setActiveTab(self):
        self._tab_attachments.setActive()


class WPCategoryAttachments(AttachmentsMixin, WPCategoryModifBase):
    base_wp = WPCategoryModifBase

    def _setActiveSideMenuItem(self):
        self.extra_menu_items['attachments'].setActive()


class WPEventAttachments(AttachmentsMixin, WPConferenceModifBase):
    base_wp = WPConferenceModifBase

    def _setActiveSideMenuItem(self):
        self.extra_menu_items['attachments'].setActive()


class WPSessionAttachments(EventObjectAttachmentsMixin, WPSessionModifBase):
    base_wp = WPSessionModifBase


class WPContributionAttachments(EventObjectAttachmentsMixin, WPContributionModifBase):
    base_wp = WPContributionModifBase


class WPSubContributionAttachments(EventObjectAttachmentsMixin, WPSubContributionModifBase):
    base_wp = WPSubContributionModifBase


class WPEventFolderDisplay(WPMeetingDisplay, WPJinjaMixin):
    template_prefix = 'attachments/'

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)


class WPPackageEventAttachmentsManagement(WPEventAttachments, WPJinjaMixin):
    template_prefix = 'attachments/'

    def _getTabContent(self, params):
        return WPJinjaMixin._getPageContent(self, params)


class WPPackageEventAttachmentsDisplayConference(WPConferenceDefaultDisplayBase, WPJinjaMixin):
    template_prefix = 'attachments/'

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)


class WPPackageEventAttachmentsDisplay(WPMeetingDisplay, WPJinjaMixin):
    template_prefix = 'attachments/'

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)
