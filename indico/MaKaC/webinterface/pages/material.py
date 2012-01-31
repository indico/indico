# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from xml.sax.saxutils import escape, quoteattr

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.navigation as navigation
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase,WPConferenceBase,WPConferenceDefaultDisplayBase, WConfDisplayFrame
import MaKaC.conference as conference
from MaKaC.webinterface.general import strfFileSize
from MaKaC.webinterface.materialFactories import ConfMFRegistry,SessionMFRegistry,ContribMFRegistry
from MaKaC.common.Configuration import Config
from MaKaC.webinterface.pages.category import WPCategoryBase,WPCategoryDisplayBase,WPCategoryDisplay
import MaKaC.webinterface.pages.category
import MaKaC.webinterface.displayMgr as displayMgr
from MaKaC.i18n import _
from indico.util.i18n import i18nformat

class WPMaterialBase( WPConferenceModifBase, WPCategoryBase ):

    def __init__( self, rh, material ):
        self._material = self._target = material
        if self._material.getConference()!=None:
            WPConferenceModifBase.__init__( self, rh, self._material.getConference() )
        else:
            WPCategoryBase.__init__(self,rh,self._material.getCategory())

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


class WPMaterialDisplayBase( WPConferenceDefaultDisplayBase ):

    def __init__(self, rh, material):
        self._material = self._target =material
        WPConferenceDefaultDisplayBase.__init__( self, rh, self._material.getConference() )
        self._navigationTarget = self._material

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
               self._includeJSPackage('MaterialEditor')

    def _applyDecoration( self, body ):
        return WPConferenceDefaultDisplayBase._applyDecoration( self, body )

    def _getBody( self, params ):

        wc = WMaterialDisplay( self._getAW(), self._material )
        pars = { "fileAccessURLGen": urlHandlers.UHFileAccess.getURL }
        return wc.getHTML( pars )


class WPMaterialCatDisplayBase(WPCategoryDisplayBase, WPMaterialDisplayBase ):
    def __init__(self, rh, material):
        self._material = self._target =material


        WPCategoryDisplayBase.__init__(self,rh,self._material.getCategory())
        self._navigationTarget = self._material

    def _applyDecoration( self, body ):

        return WPCategoryDisplayBase._applyDecoration( self, body )

    def _getBody( self, params ):

        wc = WMaterialDisplay( self._getAW(), self._material )
        pars = { "fileAccessURLGen": urlHandlers.UHFileAccess.getURL }
        return wc.getHTML( pars )


class WPMaterialConfDisplayBase(WPMaterialDisplayBase, WPConferenceDefaultDisplayBase ):

    def __init__(self,rh,material):
        self._material = self._target =material

        WPConferenceDefaultDisplayBase.__init__(self,rh,self._material.getConference())

        self._navigationTarget = self._material

    def _applyDecoration( self, body ):

        return WPConferenceDefaultDisplayBase._applyDecoration( self, body )



class WMaterialDisplay(wcomponents.WTemplated):

    def __init__(self, aw, material):
        self._material=material
        self._aw=aw

    def _canSubmitResource(self, material):
        if isinstance(material.getOwner(), conference.Contribution):
            contrib=material.getOwner()
            status=contrib.getCurrentStatus()
            if not isinstance(status,conference.ContribStatusWithdrawn) and \
                                contrib.canUserSubmit(self._aw.getUser()):
                return True
        return False

    def _getURL(self, resource):
        url = resource.getURL()
        if url.find(".wmv") != -1:
            url = urlHandlers.UHVideoWmvAccess().getURL(resource)
        elif url.find(".flv") != -1 or url.find(".f4v") != -1 or url.find("rtmp://") != -1:
            url = urlHandlers.UHVideoFlashAccess().getURL(resource)
        return url

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["canSubmitResource"] = self._canSubmitResource(self._material)
        vars["material"] = self._material
        vars["accessWrapper"] = self._aw
        vars["getURL"] = lambda resource : self._getURL(resource)
        if self._material.getSubContribution():
            vars["uploadAction"] = 'Indico.Urls.UploadAction.subcontribution'
        elif self._material.getContribution():
            vars["uploadAction"] = 'Indico.Urls.UploadAction.contribution'
        elif self._material.getSession():
            vars["uploadAction"] = 'Indico.Urls.UploadAction.session'
        elif self._material.getConference():
            vars["uploadAction"] = 'Indico.Urls.UploadAction.conference'
        else:
            vars["uploadAction"] = 'Indico.Urls.UploadAction.category'

        return vars


class WPMaterialModifBase( WPMaterialBase ):

    def _getNavigationDrawer(self):
        if self._conf is None:
            target = self._material.getCategory()
        else:
            target = self._conf.getOwner()

        pars = {"target": target, "isModif": True}
        return wcomponents.WNavigationDrawer( pars )

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHMaterialModification.getURL( self._material ) )
        self._tabAC = self._tabCtrl.newTab( "ac", _("Protection"), \
                urlHandlers.UHMaterialModifAC.getURL( self._material ) )
        self._setActiveTab()

    def _setActiveTab( self ):
        pass

    def _applyFrame( self, body ):
        frame = wcomponents.WMaterialModifFrame( self._material, self._getAW() )
        p = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
            "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL, \
            "confModifURLGen": urlHandlers.UHConferenceModification.getURL, \
            "sessionDisplayURLGen": urlHandlers.UHSessionDisplay.getURL, \
            "sessionModifURLGen": urlHandlers.UHSessionModification.getURL, \
            "materialDisplayURLGen": urlHandlers.UHMaterialDisplay.getURL, \
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


class WMaterialModifMain( wcomponents.WTemplated ):

    def __init__( self, mat ):
        self._material = mat

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["locator"] = self._material.getLocator().getWebForm()
        vars["title"] = self._material.getTitle()
        vars["description"] = self._material.getDescription()
        vars["type"] = self._material.getType()
        l = []
        for res in self._material.getResourceList():
            if res.__class__ is conference.LocalFile:
                l.append( """<li><input type="checkbox" name="removeResources" value="%s"><small>[%s]</small> <b><a href="%s">%s</a></b> (%s) - <small>%s - %s</small></li>"""%(res.getId(), res.getFileType(), vars["modifyFileURLGen"](res), res.getName(), res.getFileName(), strfFileSize( res.getSize() ),  res.getCreationDate().strftime("%d.%m.%Y %H:%M:%S") ))
            elif res.__class__ is conference.Link:
                l.append( """<li><input type="checkbox" name="removeResources" value="%s"><b><a href="%s">%s</a></b> (%s)</li>"""%(res.getId(), vars["modifyLinkURLGen"](res), res.getName(), res.getURL()))
        vars["resources"] = "<ol>%s</ol>"%"".join( l )
        mr = self._material.getMainResource()
        if mr == None:
            vars["mainResource"] = i18nformat("""--_("no main resource")--""")
        else:
            if mr.__class__ is conference.LocalFile:
                vars["mainResource"] =  """<small>[%s]</small> <b>%s</b> (%s) - <small>%s</small></li>"""%(mr.getFileType(), mr.getName(), mr.getFileName(), strfFileSize( mr.getSize() ) )
            elif mr.__class__ is conference.Link:
                vars["mainResource"] = """<b>%s</b> (%s)</li>"""%(mr.getName(), mr.getURL())
        vars["selectMainResourceURL"] = quoteattr(str(urlHandlers.UHMaterialMainResourceSelect.getURL( self._material ) ) )
        return vars


class WPMaterialModification( WPMaterialModifBase ):

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):
        wc = WMaterialModifMain( self._material )
        pars = { \
"modifyFileURLGen": urlHandlers.UHFileModification.getURL, \
"modifyLinkURLGen": urlHandlers.UHLinkModification.getURL, \
"dataModificationURL": urlHandlers.UHMaterialModifyData.getURL( self._material ), \
"removeResourcesURL": urlHandlers.UHMaterialRemoveResources.getURL(), \
"linkFilesURL": urlHandlers.UHMaterialLinkCreation.getURL( self._material ), \
"addFilesURL": urlHandlers.UHMaterialFileCreation.getURL( self._material ) }
        return wc.getHTML( pars )


class WMaterialDataModification(wcomponents.WMaterialDataModificationBase):

    def getVars( self ):
        vars = wcomponents.WMaterialDataModificationBase.getVars( self )
        vars["locator"] = self._material.getLocator().getWebForm()
        vars["title"] = self._material.getTitle()
        vars["description"] = self._material.getDescription()
        vars["types"] = self._getTypesSelectItems( self._material.getType() )
        return vars


class WPMaterialDataModification( WPMaterialModification ):

    def _getTabContent( self, params ):
        wc = WMaterialDataModification( self._material )
        pars = { "postURL": urlHandlers.UHMaterialPerformModifyData.getURL() }
        return wc.getHTML( pars )


class WLinkSubmission(wcomponents.WTemplated):

    def __init__(self, material):
        self.__material = material

    def getHTML( self, params ):
        str = """
            <form action="%s" method="POST" enctype="multipart/form-data">
                %s
                %s
            </form>
              """%(params["postURL"], \
                   self.__material.getLocator().getWebForm(),\
                   wcomponents.WTemplated.getHTML( self, params ) )
        return str

    def submit( self, params ):
        l = conference.Link()
        l.setName( params["title"] )
        l.setDescription( params["description"] )
        l.setURL( params["url"] )
        self.__material.addResource( l )
        return "[done]"


class WPMaterialLinkCreation( WPMaterialModification ):

    def _getTabContent( self, params ):
        comp = WLinkSubmission( self._material )
        pars = { "postURL": urlHandlers.UHMaterialPerformLinkCreation.getURL() }
        return comp.getHTML( pars )


class WFileSubmission(wcomponents.WTemplated):

    def __init__(self, material):
        self.__material = material

    def getHTML( self, params ):
        str = """
            <form action="%s" method="POST" enctype="multipart/form-data">
                %s
                %s
            </form>
              """%(params["postURL"], \
                   self.__material.getLocator().getWebForm(),\
                   wcomponents.WTemplated.getHTML( self, params ) )
        return str

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["conversion"]=""
        if Config.getInstance().hasFileConverter():
            vars["conversion"]= i18nformat("""
                                <tr>
                                    <td nowrap class="titleCellTD"><span class="titleCellFormat"> _("To PDF")</span></td>
                                    <td align="left"><input type="checkbox" name="topdf" checked="checked"> _("Automatic conversion to pdf (when applicable)? (PPT, DOC)")</td>
                                </tr>
                                """)
        return vars


class WPMaterialFileCreation( WPMaterialModification ):

    def _getTabContent( self, params ):
        comp = WFileSubmission( self._material )
        pars = { "postURL": urlHandlers.UHMaterialPerformFileCreation.getURL() }
        return comp.getHTML( pars )


class WMaterialModifAC( wcomponents.WTemplated ):

    def __init__( self, mat ):
        self.__target = self.__material = mat

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        if self.__target.getAccessProtectionLevel() == -1:
            vars["privacy"] = "ABSOLUTELY PUBLIC%s" % wcomponents.WInlineContextHelp('The object will stay public regardless of the protection of its parent (no more inheritance)').getHTML()
            vars["changePrivacy"] = """make it simply <input type="submit" class="btn" name="visibility" value="PUBLIC">%s<br/>""" % wcomponents.WInlineContextHelp('It will then be public by default but will inherit from the potential protection of its parent').getHTML()
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="PRIVATE"> by itself%s<br/>""" % wcomponents.WInlineContextHelp('It will then be private').getHTML()
        elif self.__target.isItselfProtected():
            vars["privacy"] = "PRIVATE%s" % wcomponents.WInlineContextHelp('The object is private by itself').getHTML()
            vars["changePrivacy"] = """make it simply <input type="submit" class="btn" name="visibility" value="PUBLIC">%s<br/>""" % wcomponents.WInlineContextHelp('It will then be public by default but will inherit from the potential protection of its parent').getHTML()
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="ABSOLUTELY PUBLIC">%s""" % wcomponents.WInlineContextHelp('The object will stay public regardless of the protection of its parent').getHTML()
        elif self.__target.hasProtectedOwner():
            vars["privacy"] = "PRIVATE by inheritance%s" % wcomponents.WInlineContextHelp('Private because a parent object is private').getHTML()
            vars["changePrivacy"] = """make it <input type="submit" class="btn" name="visibility" value="PRIVATE"> by itself%s<br/>""" % wcomponents.WInlineContextHelp('It will then remain private even if the parent object goes public').getHTML()
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="ABSOLUTELY PUBLIC">%s""" % wcomponents.WInlineContextHelp('The object will stay public regardless of the protection of its parent').getHTML()
        else:
            vars["privacy"] = "PUBLIC%s" % wcomponents.WInlineContextHelp('the object is currently public because its parent is public but might inherit from the potential protection of its parent if it changes one day').getHTML()
            vars["changePrivacy"] = """make it <input type="submit" class="btn" name="visibility" value="PRIVATE"> by itself<br/>"""
            vars["changePrivacy"] += """make it <input type="submit" class="btn" name="visibility" value="ABSOLUTELY PUBLIC">%s""" % wcomponents.WInlineContextHelp('The object will stay public regardless of the protection of its parent').getHTML()
        vars["visibility"] = "VISIBLE"
        oppVisibility = "HIDDEN"
        if self.__material.isHidden():
            vars["visibility"] = _("HIDDEN")
            oppVisibility = _("VISIBLE")
        #Privacy of the current target can only be changed if the target
        #   owner is not protected
        vars["changeVisibility"] = i18nformat("""( _("make it") <input type="submit" class="btn" name="visibility" value="%s">)""")%oppVisibility
        vars["locator"] = self.__material.getLocator().getWebForm()
        vars["userTable"] = wcomponents.WPrincipalTable().getHTML( self.__material.getAllowedToAccessList(), self.__material, vars["addAllowedURL"], vars["removeAllowedURL"] )
        vars["accessKey"] = self.__material.getAccessKey()
        vars["setAccessKeyURL"] =  urlHandlers.UHMaterialSetAccessKey.getURL()
        if not self.__material.isProtected():
            df =  wcomponents.WDomainControlFrame( self.__material )
            vars["domainControlFrame"] = "<br>%s"%df.getHTML( \
                                                    vars["addDomainURL"], \
                                                    vars["removeDomainURL"] )
        else:
            vars["domainControlFrame"] = ""
        return vars


class WPMaterialModifAC( WPMaterialModifBase ):

    def _setActiveTab( self ):
        self._tabAC.setActive()

    def _getTabContent( self, params ):
        wc = WMaterialModifAC( self._material )
        pars = { \
        "setPrivacyURL": urlHandlers.UHMaterialSetPrivacy.getURL(), \
        "setVisibilityURL": urlHandlers.UHMaterialSetVisibility.getURL(), \
        "addAllowedURL": urlHandlers.UHMaterialSelectAllowed.getURL(), \
        "removeAllowedURL": urlHandlers.UHMaterialRemoveAllowed.getURL(), \
        "addDomainURL": urlHandlers.UHMaterialAddDomains.getURL(), \
        "removeDomainURL": urlHandlers.UHMaterialRemoveDomains.getURL() }
        return wc.getHTML( pars )


class WPMaterialSelectAllowed( WPMaterialModifAC ):

    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHMaterialSelectAllowed.getURL(),forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHMaterialAddAllowed.getURL()
        return wc.getHTML( params )

class WPMaterialMainResourceSelect( WPMaterialModification ):

    def _getTabContent( self, params ):
        wc = WMaterialMainResourceSelect( self._material )
        pars = { "postURL": urlHandlers.UHMaterialMainResourcePerformSelect.getURL(self._material) }
        return wc.getHTML( pars )

class WMaterialMainResourceSelect(wcomponents.WTemplated):

    def __init__(self, material):
        self._material = material

    def _getResources(self):
        mr = self._material.getMainResource()
        checked = ""
        if mr == None:
            checked = """ checked="checked" """
        l = [ i18nformat("""<li><input type="radio" %s name="mainResource" value="none"><b> --_("no main resource")--</b></li>""")%checked]
        for res in self._material.getResourceList():
            checked = ""
            if mr != None and res.getId() == mr.getId():
                checked = """ checked="checked" """
            if res.__class__ is conference.LocalFile:
                l.append( """<li><input type="radio" %s name="mainResource" value="%s"><small>[%s]</small> <b>%s</b> (%s) - <small>%s</small></li>"""%(checked, res.getId(), res.getFileType(), res.getName(), res.getFileName(), strfFileSize( res.getSize() )))
            elif res.__class__ is conference.Link:
                l.append( """<li><input type="radio" %s name="mainResource" value="%s"><b>%s</b> (%s)</li>"""%(checked, res.getId(), res.getName(), res.getURL()))
        return "<ol>%s</ol>"%"".join( l )

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["resources"] = self._getResources()
        return vars
