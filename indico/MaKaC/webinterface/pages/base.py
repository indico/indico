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

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.common.Configuration import Config
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.i18n import _

class WPBase:
    """
    """
    _title = "Indico"

    def __init__( self, rh ):
        self._rh = rh
        self._locTZ = ""

        #store page specific CSS and JS
        self._extraCSSFiles = []
        self._extraCSS = []
        self._extraJS = []

    def _includeJSPackage(self, packageName, module = 'indico'):
        info = HelperMaKaCInfo().getMaKaCInfoInstance()

        if info.isDebugActive():
            return ['js/%s/%s/Loader.js' % (module, packageName)]
        else:
            return ['js/%s/pack/%s.pack.js' % (module, packageName)]

    def _includePresentationFiles(self):
        info = HelperMaKaCInfo().getMaKaCInfoInstance()

        if info.isDebugActive():
            return ['js/presentation/Loader.js']
        else:
            return ['js/presentation/pack/Presentation.pack.js']

    def _getBaseURL( self ):
        return Config.getInstance().getBaseURL()

    def _getTitle( self ):
        return self._title

    def _setTitle( self, newTitle ):
        self._title = newTitle.strip()

    def getJSFiles(self):
        return self._includePresentationFiles() + \
               self._includeJSPackage('Core') + \
               self._includeJSPackage('Legacy') + \
               self._includeJSPackage('Common')


    def _getJavaScriptInclude(self, scriptPath):
        return '<script src="'+ scriptPath +'" type="text/javascript"></script>\n'

    def _includeFavIds(self):
        return False

    def _includeFavList(self):
        return False

    def _getHeadContent( self ):
        """
        Returns _additional_ content between <head></head> tags.
        Please note that <title>, <meta> and standard CSS are always included.

        Override this method to add your own, page-specific loading of
        JavaScript, CSS and other legal content for HTML <head> tag.
        """
        return ""

    def _getWarningMessage(self):
        return ""

    def _getHTMLHeader( self ):
        from MaKaC.webinterface.pages.conferences import WPConfSignIn
        from MaKaC.webinterface.pages.signIn import WPSignIn
        from MaKaC.webinterface.pages.registrationForm import WPRegistrationFormSignIn
        from MaKaC.webinterface.rh.base import RHModificationBaseProtected
        from MaKaC.webinterface.rh.admins import RHAdminBase

        baseurl = self._getBaseURL()
        if ((isinstance(self, WPSignIn) or isinstance(self, WPConfSignIn) or isinstance(self, WPRegistrationFormSignIn)) and \
                Config.getInstance().getLoginURL().startswith("https")) or \
                self._rh._req.is_https() and self._rh._tohttps:
            baseurl = baseurl.replace("http://","https://")
            baseurl = urlHandlers.setSSLPort( baseurl )

        area=""
        if isinstance(self._rh, RHModificationBaseProtected):
            area=_(""" - _("Management area")""")
        elif isinstance(self._rh, RHAdminBase):
            area=_(""" - _("Administrator area")""")

        websession = self._getAW().getSession()
        if websession:
            language = websession.getLang()
        else:
            info = HelperMaKaCInfo().getMaKaCInfoInstance()
            language = info.getLang()

        return wcomponents.WHTMLHeader().getHTML({
                            "area": area,
                            "baseurl": baseurl,
                            "conf": Config.getInstance(),
                            "page": self,
                            "extraCSSFiles": self._extraCSSFiles,
                            "extraCSS": self._extraCSS,
                            "extraJSFiles": self.getJSFiles(),
                            "extraJS": self._extraJS,
                            "language": language
                            })

    def _getHTMLFooter( self ):
        return """
    </body>
</html>
               """

    def _display( self, params ):
        """
        """
        return _("no content")

    def _getAW( self ):
        return self._rh.getAW()

    def display( self, **params ):
        """
        """
        return "%s%s%s"%( self._getHTMLHeader(), \
                            self._display( params ), \
                            self._getHTMLFooter() )

    def addExtraCSSFile(self, filename):
        self._extraCSSFiles.append(filename)

    def addExtraCSS(self, cssCode):
        self._extraCSS.append(cssCode)

    def addExtraJSFile(self, filename):
        self._extraJSFiles.append(filename)

    def addExtraJS(self, jsCode):
        self._extraJS.append(jsCode)

    # auxiliar functions
    def _escapeChars(self, text):
        return text.replace('%','%%')


class WPDecorated( WPBase ):

    def _getSiteArea(self):
        return "DisplayArea"

    def getLoginURL( self ):
        return urlHandlers.UHSignIn.getURL("%s"%self._rh.getCurrentURL())

    def getLogoutURL( self ):
        return urlHandlers.UHSignOut.getURL("%s"%self._rh.getCurrentURL())

    def getLoginAsURL( self ):
        return urlHandlers.UHLogMeAs.getURL("%s"%self._rh.getCurrentURL())


    def _getHeader( self ):
        """
        """
        wc = wcomponents.WHeader( self._getAW(), isFrontPage=self._isFrontPage(), currentCategory=self._currentCategory(), locTZ=self._locTZ )
        return wc.getHTML( { "subArea": self._getSiteArea(), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())),\
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())),\
                             "loginAsURL": self.getLoginAsURL() } )

    def _getTabControl(self):
        return None

    def _getFooter( self):
        """
        """
        wc = wcomponents.WFooter(isFrontPage=self._isFrontPage())
        return wc.getHTML({ "subArea": self._getSiteArea() })

    def _applyDecoration( self, body ):
        """
        """
        return "<div class=\"wrapper\">%s%s<div class=\"emptyFooter\"></div></div>%s"%( self._getHeader(), body, self._getFooter() )

    def _display( self, params ):

        return self._applyDecoration( self._getBody( params ) )

    def _getBody( self, params ):
        """
        """
        pass

    def _getNavigationDrawer(self):
        return None

    def _isFrontPage(self):
        """
            Welcome page class overloads this, so that additional info (news, policy)
            is shown.
        """
        return False

    def _isRoomBooking(self):
        return False

    def _currentCategory(self):
        """
            Whenever in category display mode this is overloaded with the current category
        """
        return None

    def _getSideMenu(self):
        """
            Overload and return side menu whenever there is one
        """
        return None

class WPNotDecorated( WPBase ):

    def getLoginURL( self ):
        return urlHandlers.UHSignIn.getURL("%s"%self._rh.getCurrentURL())

    def getLogoutURL( self ):
        return urlHandlers.UHSignOut.getURL("%s"%self._rh.getCurrentURL())

    def _display( self, params ):
        return self._getBody( params )

    def _getBody( self, params ):
        """
        """
        pass

    def _getNavigationDrawer(self):
        return None



