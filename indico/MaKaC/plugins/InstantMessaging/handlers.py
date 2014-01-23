# -*- coding: utf-8 -*-
##
## $id$
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

from MaKaC.services.implementation.base import ProtectedModificationService, ParameterManager
from MaKaC.plugins import Observable
from MaKaC.conference import ConferenceHolder


class ChatroomServiceBase ( ProtectedModificationService, Observable ):

    def __init__(self, params):
        ProtectedModificationService.__init__(self, params)

    def _checkParams(self):
        pm = ParameterManager(self._params)
        self._conferenceID = pm.extract("conference", pType=str, allowEmpty = False)
        self._target = ConferenceHolder().getById(self._conferenceID)

        pm = ParameterManager(self._params.get('chatroomParams'))
        self._title = pm.extract('title', pType=str, allowEmpty = False)
        self._createdInLocalServer = pm.extract('createdInLocalServer', pType=bool, allowEmpty = True)

        self._showRoom = pm.extract('showRoom', pType=bool, allowEmpty = True)

