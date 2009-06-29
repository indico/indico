from MaKaC.webinterface.pages.main import WPMainBase
import MaKaC.webinterface.urlHandlers as urlHandlers

import MaKaC.webinterface.personalization as wclasses

from MaKaC.webinterface import wcomponents

class WPDisplayUserEvents( WPMainBase):

    def __init__( self, rh):
        WPMainBase.__init__(self, rh)
        self._av = self._getAW().getUser()


    def _setActiveTab( self ):
        self._tabMyEvents.setActive()

    def _getBody( self, params ):
       p = wclasses.WPersonalEvents(self._av)
        
       pars = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
                "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL }
        
       return p.getHTML( pars )

    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer("My Indico", urlHandlers.UHGetUserEventPage.getURL )