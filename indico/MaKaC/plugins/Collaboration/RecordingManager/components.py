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

from zope.interface import implements

from indico.core.extpoint import Component
from indico.core.extpoint.events import IEventDisplayContributor
from MaKaC.plugins.Collaboration.RecordingManager.output import RecordingManagerMarcTagGenerator

class RecordingManagerContributor(Component):

    implements(IEventDisplayContributor)

    @classmethod
    def addXMLMetadata(cls, obj, params):
        out = params['out']
        elem = params['obj']
        elemType = params['type']
        recordingManagerTags = params['recordingManagerTags']
        if recordingManagerTags is not None:
            # Only create these tags if this conference is the desired talk.
            if recordingManagerTags["talkType"] == elemType and recordingManagerTags["talkId"] == elem.getId():
                RecordingManagerMarcTagGenerator.generateAccessListXML(out, elem)                # MARC 506__a,d,f,2,5
                RecordingManagerMarcTagGenerator.generateVideoXML(out, recordingManagerTags)     # MARC 300__a,b
                RecordingManagerMarcTagGenerator.generateLanguagesXML(out, recordingManagerTags) # MARC 041__a
                RecordingManagerMarcTagGenerator.generateCDSCategoryXML(out, elem)               # MARC 980__a
                RecordingManagerMarcTagGenerator.generateExperimentXML(out, elem)                # MARC 693__e


