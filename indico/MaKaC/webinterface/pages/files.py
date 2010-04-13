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
from MaKaC.webinterface.pages.conferences import WPConferenceBase, WPConferenceModifBase, WPConferenceDefaultDisplayBase
from MaKaC.common.Configuration import Config
import MaKaC.webinterface.navigation as navigation
from MaKaC.webinterface.general import strfFileSize
from MaKaC.webinterface.pages.base import WPNotDecorated
from MaKaC.webinterface.pages.category import WPCategoryBase
import MaKaC.webinterface.pages.category
from MaKaC.i18n import _


class WPFileBase( WPConferenceModifBase, WPCategoryBase):
    
    def __init__( self, rh, file ):
        self._file = file
        
        if self._file.getConference()!=None:
            
            WPConferenceModifBase.__init__( self, rh, self._file.getConference() )
        
        else:
            WPCategoryBase.__init__(self,rh,self._file.getCategory())
            
 
            
        
        
class WPFileDisplayBase( WPConferenceDefaultDisplayBase ):
    def __init__(self, rh, file):
        self._file = file
        
        WPConferenceDefaultDisplayBase.__init__( self, rh, self._file.getConference() )
        self._navigationTarget = file


class WPVideoWmv( WPFileBase ):

    def _getBody( self, params ):
        return WVideoWmv(self._file).getHTML()

class WVideoWmv( wcomponents.WTemplated ):
    
    def __init__( self, file ):
        self._file = file

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["url"] = self._file.getURL()
        vars["downloadurl"] = self._file.getURL().replace("mms://","http://")
        return vars

class WPVideoFlash( WPFileBase ):

    def _getBody( self, params ):
        return WVideoFlash(self._file).getHTML()

class WVideoFlash( wcomponents.WTemplated ):
    
    def __init__( self, file ):
        self._file = file

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["indicobaseurl"] = Config.getInstance().getBaseURL()
        url = vars["url"] = self._file.getURL()
        vars["download"] = ""
        if url.find("http://") != -1:
            vars["download"] = """<a href="%s">Download File</a>""" % url
        return vars
    
class WPFileModifBase( WPFileBase ):
  
    def _getNavigationDrawer(self):
        if self._conf is None:
            target = self._file.getCategory()
        else:
            target = self._conf.getOwner()
            
        pars = {"target": target, "isModif": True}
        return wcomponents.WNavigationDrawer( pars )

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHFileModification.getURL( self._file ) )
        self._tabAC = self._tabCtrl.newTab( "ac", _("Protection"), \
                urlHandlers.UHFileModifAC.getURL( self._file ) )
        self._setActiveTab()
      
    def _setActiveTab( self ):
        pass

    def _applyFrame( self, body ):
        frame = wcomponents.WFileModifFrame( self._file, self._getAW() )
        p = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
            "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL, \
            "confModifURLGen": urlHandlers.UHConferenceModification.getURL, \
            "sessionDisplayURLGen": urlHandlers.UHSessionDisplay.getURL, \
            "sessionModifURLGen": urlHandlers.UHSessionModification.getURL, \
            "materialDisplayURLGen": urlHandlers.UHMaterialDisplay.getURL, \
            "materialModifURLGen": urlHandlers.UHMaterialModification.getURL, \
            "contribDisplayURLGen": urlHandlers.UHContributionDisplay.getURL, \
            "contribModifURLGen": urlHandlers.UHContributionModification.getURL, \
            "subContribModifURLGen": urlHandlers.UHSubContributionModification.getURL, \
            "subContribDisplayURLGen": urlHandlers.UHSubContributionDisplay.getURL}
        return frame.getHTML( body, **p )

    def _getBody( self, params ):
        self._createTabCtrl()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return self._applyFrame( html )

    def _getTabContent( self, params ):
        return "nothing"


class WFileModifMain( wcomponents.WTemplated ):
    
    def __init__( self, file ):
        self._file = file

    def getVars( self ):
        
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self._file.getName()
        vars["description"] = self._file.getDescription()
        vars["type"] = self._file.getFileType()
        vars["typeDesc"] = Config.getInstance().getFileTypeDescription( self._file.getFileType() )
        vars["downloadImg"] = Config.getInstance().getSystemIconURL("download")
        vars["fileName"] = self._file.getFileName()
        vars["fileSize"] = strfFileSize( self._file.getSize() )
        
        return vars


class WPFileModification( WPFileModifBase ):
    
    def _setActiveTab( self ):
        self._tabMain.setActive()
    
    def _getTabContent( self, params ):
        wc = WFileModifMain( self._file )
        pars = { \
    "fileAccessURL": urlHandlers.UHFileAccess.getURL( self._file ), \
    "modifyURL": urlHandlers.UHFileModifyData.getURL( self._file ) }
        return wc.getHTML( pars )


class WFileDataModification(wcomponents.WResourceDataModification): 
    pass

    
class WPFileDataModification( WPFileModifBase ):
    
    def _setActiveTab( self ):
        self._tabMain.setActive()
    
    def _getTabContent( self, params ):
        wc = WFileDataModification( self._file )
        pars = { "postURL": urlHandlers.UHFilePerformModifyData.getURL() }
        return wc.getHTML( pars )


class WFileModifAC( wcomponents.WTemplated ):
    
    def __init__( self, file ):
        self._file = file

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["accessControlFrame"] = wcomponents.WAccessControlFrame().getHTML(\
                                                    self._file,\
                                                    vars["setVisibilityURL"],\
                                                    vars["addAllowedURL"],\
                                                    vars["removeAllowedURL"] )
        return vars


class WPFileModifAC( WPFileModifBase ):
    
    def _setActiveTab( self ):
        self._tabAC.setActive()
    
    def _getTabContent( self, params ):
        wc = WFileModifAC( self._file )
        pars = { \
    "setVisibilityURL": urlHandlers.UHFileSetVisibility.getURL() , \
    "addAllowedURL": urlHandlers.UHFileSelectAllowed.getURL(), \
    "removeAllowedURL": urlHandlers.UHFileRemoveAllowed.getURL() }
        return wc.getHTML( pars )


class WPFileSelectAllowed( WPFileModifAC ):
    
    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHFileSelectAllowed.getURL(),forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHFileAddAllowed.getURL()
        return wc.getHTML( params )

#class WPFileDisplayModification( WPFileDisplayBase ):
#    navigationEntry = navigation.NEFileDisplayModification
#    
#    def _getBody( self, params ):
#        wc = WFileDisplayModification( self._file )
#        pars = { \
#            "fileAccessURL": urlHandlers.UHFileAccess.getURL( self._file ), \
#            "modifyURL": urlHandlers.UHFileDisplayDataModification.getURL( self._file ) }
#        return wc.getHTML( pars )
#
#class WFileDisplayModification(wcomponents.WTemplated):
#    
#    def __init__( self, file ):
#        self._file = file
#
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        vars["title"] = self._file.getName()
#        vars["description"] = self._file.getDescription()
#        vars["type"] = self._file.getFileType()
#        vars["typeDesc"] = Config.getInstance().getFileTypeDescription( self._file.getFileType() )
#        vars["fileName"] = self._file.getFileName()
#        vars["fileSize"] = strfFileSize( self._file.getSize() )
#        return vars
#
#class WPFileDisplayDataModification( WPFileDisplayBase ):
#    navigationEntry = navigation.NEFileDisplayModification
#    
#    def _getBody( self, params ):
#        wc = WFileDisplayDataModification( self._file )
#        pars = { "postURL": urlHandlers.UHFileDisplayPerformDataModification.getURL() }
#        return wc.getHTML( pars )
#
#class WFileDisplayDataModification( wcomponents.WTemplated ):
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
#        return vars

class WPMinutesDisplay(WPNotDecorated):
    navigationEntry=navigation.NEMaterialDisplay

    def __init__(self,rh,file):
        WPNotDecorated.__init__(self,rh)
        self._file=file
    
    def _getBody(self,params):
        wc=wcomponents.WMinutesDisplay(self._file)
        return wc.getHTML(params)
