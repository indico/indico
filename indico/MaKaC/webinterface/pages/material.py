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

    def _applyDecoration( self, body ):
        return WPConferenceDefaultDisplayBase._applyDecoration( self, body )

    
    def _defineToolBar(self):
        edit=wcomponents.WTBItem( _("manage this contribution"),
            icon=Config.getInstance().getSystemIconURL("modify"),
            actionURL=urlHandlers.UHMaterialModification.getURL(self._material),
            enabled=self._target.canModify(self._getAW()))
        self._toolBar.addItem(edit)
    
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

    def _getSubmitButtonHTML(self):
        res=""
        if isinstance(self._material.getOwner(), conference.Contribution):
            contrib=self._material.getOwner()
            status=contrib.getCurrentStatus()
            if not isinstance(status,conference.ContribStatusWithdrawn) and \
                                contrib.canUserSubmit(self._aw.getUser()):
                res= _("""<input type="submit" class="btn" value='_("submit resource")'>""")
        return res

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars( self )
        contrib=None
        mf=None
        if isinstance(self._material.getOwner(),conference.Conference):
            mf=ConfMFRegistry().get(self._material)
        elif isinstance(self._material.getOwner(),conference.Session):
            mf=SessionMFRegistry().get(self._material)
        elif isinstance(self._material.getOwner(),conference.Contribution):
            mf=ContribMFRegistry().get(self._material)
            contrib=self._material.getOwner()
        elif isinstance(self._material.getOwner(),conference.SubContribution):
            mf=ContribMFRegistry().get(self._material)
        if mf is None:
            vars["icon"]=quoteattr(str(Config.getInstance().getSystemIconURL("material")))
            vars["title"]=self.htmlText(self._material.getTitle())
        else:
            vars["icon"]=quoteattr(str(mf.getIconURL()))
            vars["title"]=self.htmlText(self._material.getTitle())
        vars["description"]=self.htmlText(self._material.getDescription())
        rl = []
        if self._material.getResourceList()==[] or not self._material.canView(self._aw):
            vars["resources"]=""
        else:
            for res in self._material.getResourceList():
                if res.isProtected():
                    protection = """&nbsp;<img src=%s style="vertical-align: middle; border: 0;">""" % Config.getInstance().getSystemIconURL("protected")
                else:
                    protection = ""
                if type(res) is conference.Link:
                    url = res.getURL()
                    if url.find(".wmv") != -1:
                        url = urlHandlers.UHVideoWmvAccess().getURL(res)
                    elif url.find(".flv") != -1 or url.find(".f4v") != -1 or url.find("rtmp://") != -1:
                        url = urlHandlers.UHVideoFlashAccess().getURL(res)
                    if res.getName() != "" and res.getName() != res.getURL():
                        title = """<b><a href="%s">%s</a></b>""" % (url, res.getName())
                    else:
                        title = """<small><a href="%s">%s</a></small>""" % (url, res.getURL())
                    rl.append("""<tr><td align="right">[LINK]</td><td width="100%%" align="left">%s%s</td></tr>"""%(title, protection))
                else:
                    iconURL = Config.getInstance().getFileTypeIconURL( res.getFileType() )
                    iconHTML = """<img src="%s" alt="">"""%Config.getInstance().getSystemIconURL("bigfile")
                    if iconURL != "":
                        iconHTML = """<img src="%s" alt="">"""%iconURL
                    if res.getName() != res.getFileName():
                        rl.append("""
                        <tr>
                            <td align="right"> %s</td>
                            <td align="left"><b>%s</b> <small>(<a href="%s">%s</a> %s - %s)</small>%s</td></tr>
                        """%(iconHTML,res.getName(),
                                    vars["fileAccessURLGen"](res),
                                    res.getFileName(),strfFileSize(res.getSize()), res.getCreationDate().strftime("%d.%m.%Y %H:%M:%S"),protection))
                    else:
                        rl.append("""
                        <tr>
                            <td align="right"> %s</td>
                            <td align="left"><b><a href="%s">%s</a></b> <small>( %s - %s)</small>%s</td></tr>
                        """%(iconHTML,vars["fileAccessURLGen"](res),
                                    res.getFileName(),strfFileSize(res.getSize()), res.getCreationDate().strftime("%d.%m.%Y %H:%M:%S"),protection))
           
            vars["resources"] = _("""<td align="right" valign="top" class="displayField" nowrap><b> _("Resources"):</b></td>
                        <td>%s</td>""")%"".join(rl)
        vars["submitURL"]=quoteattr(str(urlHandlers.UHMaterialDisplaySubmitResource.getURL(self._material)))
        vars["submitBtn"]=self._getSubmitButtonHTML()
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
            vars["mainResource"] = _("""--_("no main resource")--""")
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
            vars["conversion"]= _("""
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
        vars["changeVisibility"] = _("""( _("make it") <input type="submit" class="btn" name="visibility" value="%s">)""")%oppVisibility
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


#class WPMaterialDisplayModification( WPMaterialDisplayBase ):
#    navigationEntry = navigation.NEMaterialDisplayModification
#
#    def __init__(self, rh, material):
#        WPMaterialDisplayBase.__init__( self, rh, material )
#        self._navigationTarget = self._material
#
#    def _getBody( self, params ):
#        wc = WMaterialDisplayModification( self._material )
#        pars = { \
#"modifyFileURLGen": urlHandlers.UHFileDisplayModification.getURL, \
#"modifyLinkURLGen": urlHandlers.UHLinkDisplayModification.getURL, \
#"dataModificationURL": urlHandlers.UHMaterialDisplayDataModification.getURL( self._material ), \
#"removeResourcesURL": urlHandlers.UHMaterialDisplayRemoveResources.getURL(self._material), \
#"linkFilesURL": urlHandlers.UHMaterialDisplayLinkCreation.getURL( self._material ), \
#"addFilesURL": urlHandlers.UHMaterialDisplayFileCreation.getURL( self._material ) }
#        return wc.getHTML( pars )

#class WMaterialDisplayModification( wcomponents.WTemplated ):
#
#    def __init__( self, mat ):
#        self._material = mat
#    
#    def getVars( self ):
#        vars = wcomponents.WTemplated.getVars( self )
#        vars["title"] = self._material.getTitle()
#        vars["description"] = self._material.getDescription()
#        vars["type"] = self._material.getType()
#        l = []
#        for res in self._material.getResourceList():
#            if res.__class__ is conference.LocalFile:
#                l.append( """<li><input type="checkbox" name="removeResources" value="%s"><small>[%s]</small> <b><a href="%s">%s</a></b> (%s) - <small>%s bytes</small></li>"""%(res.getId(), res.getFileType(), vars["modifyFileURLGen"](res), res.getName(), res.getFileName(), strfFileSize( res.getSize() )))
#            elif res.__class__ is conference.Link:
#                l.append( """<li><input type="checkbox" name="removeResources" value="%s"><b><a href="%s">%s</a></b> (%s)</li>"""%(res.getId(), vars["modifyLinkURLGen"](res), res.getName(), res.getURL()))
#        vars["resources"] = "<ol>%s</ol>"%"".join( l )
#        
#        return vars


#class WPMaterialDisplayDataModification( WPMaterialDisplayModification ):
#    
#    def _getBody( self, params ):
#        wc = WMaterialDisplayDataModification( self._material )
#        pars = { "postURL": urlHandlers.UHMaterialDisplayPerformDataModification.getURL(self._material) }
#        return wc.getHTML( pars )

#class WMaterialDisplayDataModificationBase(wcomponents.WTemplated):
#    
#    def __init__( self, material ):
#        self._material = material
#        self._owner = material.getOwner()
#   
#    def _getTypesSelectItems( self, default = "misc" ):
#        definedTypes = ["misc"]
#        l = []
#        for type in definedTypes:
#            default = ""
#            if type == default:
#                default = "default"
#            l.append("""<option value="%s" %s>%s</option>"""%( type, default, type ))
#        return "".join( l )

#class WMaterialDisplayDataModification(WMaterialDisplayDataModificationBase):
#    
#    def getVars( self ):
#        vars = WMaterialDisplayDataModificationBase.getVars( self )
#        vars["title"] = self._material.getTitle()
#        vars["description"] = self._material.getDescription()
#        vars["types"] = self._getTypesSelectItems( self._material.getType() )
#        return vars


#class WPMaterialDisplayLinkCreation( WPMaterialDisplayModification ):
#    
#    def _getBody( self, params ):
#        comp = WMaterialDisplayLinkSubmission( self._material )
#        pars = { "postURL": urlHandlers.UHMaterialDisplayPerformLinkCreation.getURL() }
#        return comp.getHTML( pars )

#class WMaterialDisplayLinkSubmission(wcomponents.WTemplated):
#    
#    def __init__(self, material):
#        self._material = material
#
#    def getHTML( self, params ):
#        str = """
#            <form action="%s" method="POST" enctype="multipart/form-data">
#                %s
#                %s
#            </form>
#              """%(params["postURL"], \
#                   self._material.getLocator().getWebForm(),\
#                   wcomponents.WTemplated.getHTML( self, params ) )
#        return str

#class WPMaterialDisplayFileCreation( WPMaterialDisplayModification ):
#    
#    def _getBody( self, params ):
#        comp = WMaterialDisplayFileSubmission( self._material )
#        pars = { "postURL": urlHandlers.UHMaterialDisplayPerformFileCreation.getURL() }
#        return comp.getHTML( pars )

#class WMaterialDisplayFileSubmission(wcomponents.WTemplated):
#    
#    def __init__(self, material):
#        self._material = material
#
#    def getHTML( self, params ):
#        str = """
#            <form action="%s" method="POST" enctype="multipart/form-data">
#                %s
#                %s
#            </form>
#              """%(params["postURL"], \
#                   self._material.getLocator().getWebForm(),\
#                   wcomponents.WTemplated.getHTML( self, params ) )
#        return str

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
        l = [ _("""<li><input type="radio" %s name="mainResource" value="none"><b> --_("no main resource")--</b></li>""")%checked]
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

class WPMaterialDisplayRemoveResourceConfirm( WPMaterialDisplayBase ):
    
    def __init__(self,rh, conf, res):
        WPMaterialDisplayBase.__init__(self,rh,conf)
        self._res=res
    
    def _getBody(self,params):
        wc=wcomponents.WDisplayConfirmation()
        msg= _(""" _("Are you sure you want to delete the following resource?")<br>
            <b><i>%s</i></b>
        <br>""")%self._res.getFileName()
        url=urlHandlers.UHMaterialDisplayRemoveResource.getURL(self._res)
        return wc.getHTML(msg,url,{})


class WMaterialDisplaySubmitResource(wcomponents.WTemplated):
    
    def __init__(self,material):
        self._material=material
        self._contrib=material.getOwner()

    def _getErrorHTML(self,errorList):
        if len(errorList)==0:
            return ""
        return """
            <tr>
                <td>&nbsp;</td>
            </tr>
            <tr>
                <td colspan="2" align="center">
                    <table bgcolor="red">
                        <tr>
                            <td bgcolor="white">
                                <font color="red">%s</font>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
            <tr>
                <td>&nbsp;</td>
            </tr>
                """%("<br>".join(errorList))

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHMaterialDisplaySubmitResource.getURL(self._material)))
        vars["contribId"]=self.htmlText(self._contrib.getId())
        vars["contribTitle"]=self.htmlText(self._contrib.getTitle())
        vars["matType"]=self._material.getId()
        vars["description"]=self.htmlText(vars.get("description",""))
        vars["errors"]=self._getErrorHTML(vars.get("errorList",[]))
        return vars


class WPMaterialDisplaySubmitResource(WPMaterialDisplayBase):
    navigationEntry=navigation.NEMaterialDisplay

    def __init__(self,rh,material):
        WPMaterialDisplayBase.__init__(self,rh,material)
    
    def _getBody(self,params):
        wc=WMaterialDisplaySubmitResource(self._material)
        return wc.getHTML(params)
