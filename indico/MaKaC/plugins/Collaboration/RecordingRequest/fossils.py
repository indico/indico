# -*- coding: utf-8 -*-
##
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

from MaKaC.fossils.contribution import IContributionWithSpeakersFossil
from MaKaC.fossils.subcontribution import ISubContributionWithSpeakersFossil
from MaKaC.common.fossilize import addFossil
from MaKaC.conference import Contribution


class IContributionRRFossil(IContributionWithSpeakersFossil):
    """ This fossil is ready for when we add subcontribution granularity to contributions
        and to provide an example for a plugin-specific fossil
    """
    
    def getSubContributionList(self):
        pass
    getSubContributionList.result = ISubContributionWithSpeakersFossil
    
# We cannot include this fossil in the Contribution class directly because it belongs to a plugin
addFossil(Contribution, IContributionRRFossil)