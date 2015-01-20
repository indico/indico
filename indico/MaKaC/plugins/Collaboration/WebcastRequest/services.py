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

from MaKaC.plugins.Collaboration.services import CollaborationPluginServiceBase
from MaKaC.plugins.Collaboration.WebcastRequest.common import getCommonTalkInformation
from MaKaC.conference import Contribution
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.contribution import IContributionWithSpeakersFossil

class WebcastAbleTalksService(CollaborationPluginServiceBase):

    def _getAnswer(self):
        talkInfo = getCommonTalkInformation(self._conf)
        webcastAbleTalks = talkInfo[3]
        webcastAbleTalks.sort(key = Contribution.contributionStartDateForSort)

        return fossilize(webcastAbleTalks, IContributionWithSpeakersFossil,
                         tz = self._conf.getTimezone(),
                         units = '(hours)_minutes',
                         truncate = True)
