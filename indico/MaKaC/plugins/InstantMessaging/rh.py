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

from MaKaC.plugins import PluginsHolder
from MaKaC.conference import ConferenceHolder
from MaKaC.plugins.helpers import DBHelpers, LogLinkGenerator
from MaKaC.plugins.InstantMessaging.pages import WPConfModifChat, WPConferenceInstantMessaging
from MaKaC.webinterface import urlHandlers
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.i18n import _
import urllib2


class RHChatModifBase(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)

        self._activeTabName = params.get("tab", None)

        self._tabs = []
        #fill the tabs with the active plugins in the Instant Messaging module
        for plugin in PluginsHolder().getPluginType('InstantMessaging').getPluginList():
            if plugin.isActive():
                  self._tabs.append(plugin.getName())


class RHChatFormModif(RHChatModifBase):
    """ For the conference modification"""
    _uh = urlHandlers.UHConfModifChat

    def _checkParams(self, params):
        RHChatModifBase._checkParams(self, params)
        if self._activeTabName and not self._activeTabName in self._tabs:
            self._cannotViewTab = True
        else:
            self._cannotViewTab = False
            if not self._activeTabName and self._tabs:
                self._activeTabName = self._tabs[0]

    def _process( self ):
        p = WPConfModifChat( self, self._conf )
        return p.display()


class RHChatSeeLogs(RHChatModifBase):
    """ For the conference modification"""
    _uh = urlHandlers.UHConfModifChatSeeLogs

    def _checkParams(self, params):
        RHChatModifBase._checkParams(self, params)
        self._conf = ConferenceHolder().getById(params['confId'])
        self._chatroom = DBHelpers.getChatroom(params['chatroom'])
        self._sdate = params['sdate'] if params.has_key('sdate') else None
        self._edate = params['edate'] if params.has_key('edate') else None
        self._forEvent = bool(params['forEvent']) if params.has_key('forEvent') else None
        self._getAll = not self._sdate and not self._edate and not self._forEvent

    def _process( self ):
        if self._getAll:
            url = LogLinkGenerator(self._chatroom).generate()
        elif self._forEvent:
            url = LogLinkGenerator(self._chatroom).generate(str(self._conf.getStartDate().date()), str(self._conf.getEndDate().date()))
        else:
            url = LogLinkGenerator(self._chatroom).generate(self._sdate, self._edate)

        req = urllib2.Request(url, None, {'Accept-Charset' : 'utf-8'})
        document = urllib2.urlopen(req).read()
        if document is '':
            return _('No logs were found for these dates')
        return document


class RHInstantMessagingDisplay(RHConferenceBaseDisplay):
    """ For the conference display"""
    _uh = urlHandlers.UHConferenceInstantMessaging

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)

    def _process( self ):
        p = WPConferenceInstantMessaging( self, self._conf )
        return p.display()

