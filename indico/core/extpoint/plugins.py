# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.


from indico.core.extpoint import IContributor


class IPluginSettingsContributor(IContributor):

    def hasPluginSettings(self, obj, ptype, plugin):
        pass

    def getPluginSettingsHTML(self, obj, ptype, plugin):
        pass


class IPluginImplementationContributor(IContributor):

    def getPluginImplementation(self, obj):
        pass


class IPluginRightsContributor(IContributor):

    def isAllowedToAccess(self, obj):
        pass

    def isPluginTypeAdmin(self, obj, params):
        pass

    def isPluginAdmin(self, obj, params):
        pass

    def isPluginManager(self, obj, params):
        pass

    def isPluginUser(self, obj, params):
        pass

    def conferencePluginManagementURL(self, obj, params):
        pass


class IPluginDocumentationContributor(IContributor):

    def providePluginDocumentation(self, obj):
        pass
