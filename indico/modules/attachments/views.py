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
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase
from MaKaC.webinterface.pages.sessions import WPSessionModifBase
from MaKaC.webinterface.pages.contributions import WPContributionModifBase
from MaKaC.webinterface.pages.subContributions import WPSubContributionModifBase


class AttachmentsMixin(WPJinjaMixin):
    template_prefix = 'attachments/'
    base_wp = None

    def _getPageContent(self, params):
        return WPJinjaMixin._getPageContent(self, params)

    def getJSFiles(self):
        return self.base_wp.getJSFiles(self) + self._asset_env['dropzone_js'].urls()

    def getCSSFiles(self):
        return self.base_wp.getCSSFiles(self) + self._asset_env['dropzone_css'].urls()


class EventObjectAttachmentsMixin(AttachmentsMixin):
    def _getPageContent(self, params):
        return self.base_wp._getPageContent(self, params)

    def _getTabContent(self, params):
        return AttachmentsMixin._getPageContent(self, params)

    def _setActiveTab(self):
        self._tab_attachments.setActive()


class WPCategoryAttachments(AttachmentsMixin, WPCategoryModifBase):
    base_wp = WPCategoryModifBase  # old-style, so we can't use super :(

    def _setActiveSideMenuItem(self):
        self.extra_menu_items['attachments'].setActive()


class WPEventAttachments(AttachmentsMixin, WPConferenceModifBase):
    base_wp = WPConferenceModifBase  # old-style, so we can't use super :(

    def _setActiveSideMenuItem(self):
        self.extra_menu_items['attachments'].setActive()


class WPSessionAttachments(EventObjectAttachmentsMixin, WPSessionModifBase):
    base_wp = WPSessionModifBase  # old-style, so we can't use super


class WPContributionAttachments(EventObjectAttachmentsMixin, WPContributionModifBase):
    base_wp = WPContributionModifBase  # old-style, so we can't use super


class WPSubContributionAttachments(EventObjectAttachmentsMixin, WPSubContributionModifBase):
    base_wp = WPSubContributionModifBase  # old-style, so we can't use super


class WPEventFolderDisplay(WPMeetingDisplay, WPJinjaMixin):
    template_prefix = 'attachments/'

    def _getBody(self, params):
        return WPJinjaMixin._getPageContent(self, params)
