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
from MaKaC.plugins.Collaboration.RecordingRequest.common import getTalks
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.contribution import IContributionWithSpeakersFossil

class RecordingAbleTalksService(CollaborationPluginServiceBase):

    def _getAnswer(self):
        talks = getTalks(self._conf, sort = True)
        return fossilize(talks, IContributionWithSpeakersFossil,
                         tz = self._conf.getTimezone(),
                         units = '(hours)_minutes',
                         truncate = True)
