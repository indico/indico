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

from MaKaC.fossils.contribution import IContributionWithSpeakersFossil
from MaKaC.fossils.subcontribution import ISubContributionWithSpeakersFossil
from MaKaC.common.fossilize import addFossil
from MaKaC.conference import Contribution
from MaKaC.plugins.Collaboration.fossils import ICSErrorBaseFossil
from MaKaC.plugins.Collaboration.base import CollaborationTools


class IContributionRRFossil(IContributionWithSpeakersFossil):
    """ This fossil is ready for when we add subcontribution granularity to contributions
        and to provide an example for a plugin-specific fossil
    """

    def getSubContributionList(self):
        pass
    getSubContributionList.result = ISubContributionWithSpeakersFossil

    def getRecordingCapable(self):
        pass
    getRecordingCapable.produce = lambda self: CollaborationTools.isAbleToBeWebcastOrRecorded(self, "RecordingRequest")

# We cannot include this fossil in the Contribution class directly because it belongs to a plugin
addFossil(Contribution, IContributionRRFossil)

class IRecordingRequestErrorFossil(ICSErrorBaseFossil):

    def getOperation(self):
        pass

    def getInner(self):
        pass
