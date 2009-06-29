from MaKaC.webinterface import wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.pages.main import WPMainBase

class WPAbout( WPMainBase ):

    def _getNavigationDrawer(self):
        return wcomponents.WSimpleNavigationDrawer("About", urlHandlers.UHAbout.getURL )

    def _getBody( self, params ):
        wc = WAbout()
        return wc.getHTML(params)

class WAbout( wcomponents.WTemplated ):
    pass