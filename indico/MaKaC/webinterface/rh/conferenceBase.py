# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from indico.util.caching import memoize_request
from indico.util.contextManager import ContextManager
from MaKaC.conference import ConferenceHolder
from MaKaC.webinterface.rh.base import RH


class RHCustomizable(RH):

    def __init__(self):
        RH.__init__(self)
        self._wf = ""

    def getWebFactory(self):
        if self._wf == '':
            self._wf = self._conf.as_event.web_factory
        return self._wf


class RHConferenceSite(RHCustomizable):
    def _checkParams(self, params):
        # getById raises a NotFoundError if the event doesn't exist
        self._conf = self._target = ConferenceHolder().getById(params['confId'])
        ContextManager.set("currentConference", self._conf)

    @property
    @memoize_request
    def event_new(self):
        return self._conf.as_event


class RHConferenceBase(RHConferenceSite):
    pass
