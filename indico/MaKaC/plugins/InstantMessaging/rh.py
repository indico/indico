from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase
from MaKaC.plugins.base import PluginsHolder
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from MaKaC.plugins.InstantMessaging.pages import WPConfModifChat, WPConferenceInstantMessaging
from MaKaC.webinterface import urlHandlers


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


class RHInstantMessagingDisplay(RHConferenceBaseDisplay):
    """ For the conference display"""
    _uh = urlHandlers.UHConferenceInstantMessaging

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)

    def _process( self ):
        p = WPConferenceInstantMessaging( self, self._conf )
        return p.display()