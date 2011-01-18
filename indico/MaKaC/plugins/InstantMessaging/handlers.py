# -*- coding: utf-8 -*-
##
## $id$
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

from MaKaC.services.implementation.base import ProtectedModificationService, ParameterManager
from MaKaC.plugins import Observable
from MaKaC.conference import ConferenceHolder


class ChatroomServiceBase ( ProtectedModificationService, Observable ):

    def __init__(self, params, remoteHost, session):
        ProtectedModificationService.__init__(self, params, remoteHost, session)

    def _checkParams(self):
        pm = ParameterManager(self._params)
        self._conferenceID = pm.extract("conference", pType=str, allowEmpty = False)
        self._target = ConferenceHolder().getById(self._conferenceID)

        pm = ParameterManager(self._params.get('chatroomParams'))
        self._title = pm.extract('title', pType=str, allowEmpty = False)
        self._createdInLocalServer = pm.extract('createdInLocalServer', pType=bool, allowEmpty = True)

        self._showRoom = pm.extract('showRoom', pType=bool, allowEmpty = True)

