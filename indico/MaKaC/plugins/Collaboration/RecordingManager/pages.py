# -*- coding: utf-8 -*-
##
## $Id: pages.py,v 1.8 2009/04/25 13:56:17 dmartinc Exp $
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

from MaKaC.plugins.Collaboration.base import WCSPageTemplateBase, WJSBase, WCSCSSBase,\
    CollaborationTools
from MaKaC.plugins.Collaboration.RecordingManager.common import getTalks, getOrphans, languageList

class WNewBookingForm(WCSPageTemplateBase):

    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )
        orphans = getOrphans()
        vars["Orphans"] = orphans
        talks = getTalks(self._conf, sort = True)
        vars["Talks"] = talks
        vars["Conference"] = self._conf
        vars["PreviewURL"] = CollaborationTools.getOptionValue("RecordingManager", "micalaPreviewURL")
        vars["LanguageList"] = languageList
        return vars

class WMain (WJSBase):
    pass

class WIndexing(WJSBase):
    pass

class WExtra (WJSBase):
    def getVars(self):
        vars = WJSBase.getVars( self )

        if self._conf:
            vars["ConferenceId"] = self._conf.getId()
        else:
            # this is so that template can still be rendered in indexes page...
            # if necessary, we should refactor the Extra.js code so that it gets the
            # conference data from the booking, now that the booking has the conference inside
            vars["ConferenceId"] = ""
        return vars

class WStyle (WCSCSSBase):
    pass
