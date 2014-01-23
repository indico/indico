# -*- coding: utf-8 -*-
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

import zope.interface
from indico.core.extpoint.base import Component
from indico.core.extpoint.events import IUserAreaContributor
from MaKaC.webinterface import wcomponents
from indico.ext import calendaring
from indico.ext.calendaring.storage import getUserDisablePluginStorage, isUserPluginEnabled


class IUserAreaComponent(Component):

    zope.interface.implements(IUserAreaContributor)

    def userPreferences(self, obj, userId):
        vars = {}
        vars['userId'] = userId
        vars['outlookPluginEnabled'] = isUserPluginEnabled(userId)
        return WPluginUserPreferences.forModule(calendaring).getHTML(vars)


class WPluginUserPreferences(wcomponents.WTemplated):

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        return vars
