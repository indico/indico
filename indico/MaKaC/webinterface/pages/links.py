# -*- coding: utf-8 -*-
##
## $Id: links.py,v 1.15 2008/10/31 17:38:14 dmartinc Exp $
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
import MaKaC.webinterface.navigation as navigation
from MaKaC.webinterface.pages.conferences import WPConferenceBase,WPConferenceDefaultDisplayBase
from MaKaC.webinterface.pages.category import WPCategoryBase
from MaKaC.i18n import _

class WPLinkBase( WPConferenceBase, WPCategoryBase ):

    def __init__( self, rh, file ):
        self._file = file
        if self._file.getConference()!=None:
            WPConferenceBase.__init__( self, rh, self._file.getConference() )
        else:
            WPCategoryBase.__init__(self,rh,self._file.getCategory())

    def _getFooter( self ):
        """
        """
        wc = wcomponents.WFooter()
        if self._conf != None:
            p = {"modificationDate":self._conf.getModificationDate().strftime("%d %B %Y %H:%M"),
                 "subArea": self._getSiteArea() }
            return wc.getHTML(p)
        else:
            return wc.getHTML()

class WPLinkDisplayBase( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, link):
        self._link = link
        WPConferenceDefaultDisplayBase.__init__( self, rh, self._link.getConference() )
        self._navigationTarget = link


class WPLinkModifBase( WPLinkBase ):

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WManagementHeader( self._getAW() )
        return wc.getHTML( { "loginURL": urlHandlers.UHSignIn.getURL("%s"%self._rh.getCurrentURL()),\
                             "logoutURL": urlHandlers.UHSignOut.getURL(),\
                             "loginAsURL": self.getLoginAsURL() } )

##        wc = wcomponents.WManagementHeader( self._getAW(), self._getNavigationDrawer() )
##        return wc.getHTML( { "loginURL": self.getLoginURL(),\
##                             "logoutURL": self.getLogoutURL() } )


    def _getNavigationDrawer(self):
        if self._conf is None:
            target = self._file.getCategory()
        else:
            target = self._parentCateg

        pars = {"target": target, "isModif": True}
        return wcomponents.WNavigationDrawer( pars )

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHLinkModification.getURL( self._file ) )
        self._tabAC = self._tabCtrl.newTab( "ac", _("Protection"), \
                urlHandlers.UHLinkModifAC.getURL( self._file ) )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _applyFrame( self, body ):
        frame = wcomponents.WLinkModifFrame( self._file, self._getAW() )
        p = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
            "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL, \
            "confModifURLGen": urlHandlers.UHConferenceModification.getURL, \
            "contribDisplayURLGen": urlHandlers.UHContributionDisplay.getURL, \
            "contribModifURLGen": urlHandlers.UHContributionModification.getURL, \
            "subContribDisplayURLGen": urlHandlers.UHSubContributionDisplay.getURL, \
            "subContribModifURLGen": urlHandlers.UHSubContributionModification.getURL, \
            "sessionDisplayURLGen": urlHandlers.UHSessionDisplay.getURL, \
            "sessionModifURLGen": urlHandlers.UHSessionModification.getURL, \
            "materialDisplayURLGen": urlHandlers.UHMaterialDisplay.getURL, \
            "materialModifURLGen": urlHandlers.UHMaterialModification.getURL }
        return frame.getHTML( body, **p )

    def _getBody( self, params ):
        self._createTabCtrl()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return self._applyFrame( html )

    def _getTabContent( self, params ):
        return "nothing"


class WLinkModifMain( wcomponents.WTemplated ):

    def __init__( self, link ):
        self._link = link

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self._link.getName()
        vars["description"] = self._link.getDescription()
        vars["url"] = self._link.getURL()
        return vars


class WPLinkModification( WPLinkModifBase ):

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):
        wc = WLinkModifMain( self._file )
        pars = { \
    "modifyURL": urlHandlers.UHLinkModifyData.getURL( self._file ) }
        return wc.getHTML( pars )


class WLinkDataModification(wcomponents.WResourceDataModification):

    def getVars( self ):
        vars = wcomponents.WResourceDataModification.getVars( self )
        vars["url"] = self._resource.getURL()
        return vars


class WPLinkDataModification( WPLinkModifBase ):

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):
        wc = WLinkDataModification( self._file )
        pars = { "postURL": urlHandlers.UHLinkPerformModifyData.getURL() }
        return wc.getHTML( pars )


class WLinkModifAC( wcomponents.WTemplated ):

    def __init__( self, link ):
        self._link = link

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["accessControlFrame"] = wcomponents.WAccessControlFrame().getHTML(\
                                                    self._link,\
                                                    vars["setVisibilityURL"],\
                                                    vars["addAllowedURL"],\
                                                    vars["removeAllowedURL"] )
        return vars


class WPLinkModifAC( WPLinkModifBase ):

    def _setActiveTab( self ):
        self._tabAC.setActive()

    def _getTabContent( self, params ):
        wc = WLinkModifAC( self._file )
        pars = { \
    "setVisibilityURL": urlHandlers.UHLinkSetVisibility.getURL() , \
    "addAllowedURL": urlHandlers.UHLinkSelectAllowed.getURL(), \
    "removeAllowedURL": urlHandlers.UHLinkRemoveAllowed.getURL() }
        return wc.getHTML( pars )


class WPLinkSelectAllowed( WPLinkModifAC ):

    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHLinkSelectAllowed.getURL(),forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHLinkAddAllowed.getURL()
        return wc.getHTML( params )


#class WPLinkDisplayModification( WPLinkDisplayBase ):
#    navigationEntry = navigation.NELinkDisplayModification
#
#    def _getBody( self, params ):
#        wc = WLinkDisplayModification( self._link )
#        pars = { \
#            "modifyURL": urlHandlers.UHLinkDisplayDataModification.getURL( self._link ) }
#        return wc.getHTML( pars )


#class WLinkDisplayModification(wcomponents.WTemplated):
#
#    def __init__( self, link ):
#        self._link = link
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        vars["title"] = self._link.getName()
#        vars["description"] = self._link.getDescription()
#        vars["url"] = self._link.getURL()
#        return vars

#class WPLinkDisplayDataModification( WPLinkDisplayBase ):
#    navigationEntry = navigation.NELinkDisplayModification
#
#    def _getBody( self, params ):
#        wc = WLinkDisplayDataModification( self._link )
#        pars = { "postURL": urlHandlers.UHLinkDisplayPerformDataModification.getURL() }
#        return wc.getHTML( pars )

#class WLinkDisplayDataModification( wcomponents.WTemplated ):
#
#    def __init__( self, resource ):
#        self._resource = resource
#
#    def getHTML(self, params):
#        str = """
#            <form action="%s" method="POST" enctype="multipart/form-data">
#                %s
#                %s
#            </form>
#              """%(params["postURL"],\
#                   self._resource.getLocator().getWebForm(),\
#                   wcomponents.WTemplated.getHTML( self, params ) )
#        return str
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        vars["title"] = self._resource.getName()
#        vars["description"] = self._resource.getDescription()
#        vars["url"] = self._resource.getURL()
#        return vars
