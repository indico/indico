# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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
from MaKaC.errors import MaKaCError
from MaKaC.i18n import _
from MaKaC.webinterface import locators
from MaKaC.webinterface.rh.base import RH


BYTES_1MB = 1024 * 1024


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
        l = locators.WebLocator()
        l.setConference( params )
        self._conf = self._target = l.getObject()
        ContextManager.set("currentConference", self._conf)

    @property
    @memoize_request
    def event_new(self):
        return self._conf.as_event


class RHConferenceBase(RHConferenceSite):
    pass


class RHFileBase(RHConferenceSite):

    def _checkParams(self, params):
        l = locators.WebLocator()
        l.setResource(params)
        self._file = self._target = l.getObject()
#        if not isinstance(self._file, LocalFile):
#            raise MaKaCError("No file found, %s found instead"%type(self._file))
        self._conf = self._file.getConference()


class RHTrackBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setTrack( params )
        self._track = self._target = l.getObject()
        self._conf = self._track.getConference()


class RHAbstractBase( RHConferenceSite ):

    def _checkParams( self, params ):
        l = locators.WebLocator()
        l.setAbstract( params )
        self._abstract = self._target = l.getObject()
        if self._abstract is None:
            raise MaKaCError( _("The abstract you are trying to access does not exist"))
        self._conf = self._abstract.getOwner().getOwner()
