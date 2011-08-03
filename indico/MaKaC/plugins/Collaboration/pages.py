# -*- coding: utf-8 -*-
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import zope.interface

from indico.core.extpoint.base import Component
from indico.core.extpoint.events import IEventDisplayContributor
from indico.util.date_time import now_utc

from MaKaC.webinterface import wcomponents
from MaKaC.plugins import Collaboration
from MaKaC.plugins.Collaboration.output import OutputGenerator
from MaKaC.common.utils import formatTwoDates


class IMEventDisplayComponent(Component):

    zope.interface.implements(IEventDisplayContributor)

    # EventDisplayContributor
    def injectCSSFiles(self, obj):
        return []

    def eventDetailBanner(self, obj, conf):
        vars = OutputGenerator.getCollaborationParams(conf)
        return WEventDetailBanner.forModule(Collaboration).getHTML(vars)


class WEventDetailBanner(wcomponents.WTemplated):

    @staticmethod
    def getBookingType(booking):
        if booking.canBeStarted():
            return "ongoing"
        elif booking.hasStartDate() and booking.getStartDate() > now_utc():
            return "scheduled"
        else:
            return ""

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars['getBookingType'] = WEventDetailBanner.getBookingType
        vars['formatTwoDates'] = formatTwoDates
        return vars