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
#from MaKaC.plugins.Collaboration.RecordingManager.common import typeOfEvents,\
#    postingUrgency, recordingPurpose, intendedAudience, subjectMatter, lectureOptions,\
#    getTalks
from MaKaC.plugins.Collaboration.RecordingManager.common import getTalks, getOrphans, languageList
from MaKaC.conference import Contribution
from MaKaC.common.timezoneUtils import isSameDay
from MaKaC.common.fossilize import fossilize
from MaKaC.common.Conversion import Conversion
from MaKaC.accessControl import AccessWrapper
from MaKaC.common.output import outputGenerator
from MaKaC.fossils.contribution import IContributionWithSpeakersFossil
from MaKaC.user import Avatar
from MaKaC.user import CERNGroup

class WNewBookingForm(WCSPageTemplateBase):

    def getVars(self):
        vars = WCSPageTemplateBase.getVars( self )

        vars["IsSingleBooking"] = not CollaborationTools.getCSBookingClass(self._pluginName)._allowMultiple
        vars["Conference"] = self._conf
        isLecture = self._conf.getType() == 'simple_event'
        vars["IsLecture"] = isLecture

        contributions = []

        booking = self._conf.getCSBookingManager().getSingleBooking('RecordingManager')

        if not isLecture and self._conf.getNumberOfContributions() > 0:


            initialDisplay = booking is not None
            vars["DisplayTalks"] = initialDisplay

            #a talk is defined as a non-poster contribution
            talks = getTalks(self._conf, oneIsEnough = 0)
            nTalks = len(talks)
            vars["HasTalks"] = nTalks > 0

            if initialDisplay:
                talks.sort(key = Contribution.contributionStartDateForSort)

                contributions = fossilize(talks, IContributionWithSpeakersFossil,
                                          tz = self._conf.getTimezone(),
                                          units = '(hours)_minutes',
                                          truncate = True)


        else:
            vars["DisplayTalks"] = booking is not None
            vars["HasTalks"] = False

        vars["Contributions"] = contributions

        orphans = getOrphans()
        vars["Orphans"] = orphans
        talks = getTalks(self._conf, sort = True)
        vars["Talks"] = talks
        vars["Conference"] = self._conf

        from MaKaC.export.oai2 import DataInt, XMLGen

        # I don't understand what the following lines do. Pedro did this for me.
        xmlGen = XMLGen()
        di = DataInt(xmlGen)
        og = outputGenerator(self._rh.getAW(), dataInt=di)

        vars["selftype"] = type(self)

        xmlGen.openTag("iconf")
        og.confToXMLMarc21(self._conf, 1, 1, 1, forceCache=True, out=xmlGen)
        xmlGen.closeTag("iconf")

        vars["marcxml"] = xmlGen.getXml()

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
            vars["NumberOfContributions"] = self._conf.getNumberOfContributions()

            # these 2 vars are used to see if contrib dates shown should include day or just time
            vars["ConfStartDate"] = Conversion.datetime(self._conf.getAdjustedStartDate())
            vars["IsMultiDayEvent"] = not isSameDay(self._conf.getStartDate(), self._conf.getEndDate(), self._conf.getTimezone())

            location = ""
            if self._conf.getLocation() and self._conf.getLocation().getName():
                location = self._conf.getLocation().getName().strip()
            vars["ConfLocation"] = location

            room = ""
            if self._conf.getRoom() and self._conf.getRoom().getName():
                room = self._conf.getRoom().getName().strip()
            vars["ConfRoom"] = room

        else:
            # this is so that template can still be rendered in indexes page...
            # if necessary, we should refactor the Extra.js code so that it gets the
            # conference data from the booking, now that the booking has the conference inside
            vars["ConferenceId"] = ""
            vars["NumberOfContributions"] = 0
            vars["ConfStartDate"] = ""
            vars["IsMultiDayEvent"] = False
            vars["ConfLocation"] = ""
            vars["ConfRoom"] = ""

        return vars

class WStyle (WCSCSSBase):
    pass
