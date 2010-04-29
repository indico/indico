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
import urllib

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.webinterface.navigation as navigation
import MaKaC.webinterface.linking as linking
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from xml.sax.saxutils import quoteattr
from MaKaC.webinterface.pages.conferences import WPConferenceDefaultDisplayBase, WPConferenceBase, WPConferenceModifBase
from MaKaC.common.Configuration import Config
from datetime import datetime
from MaKaC.common.utils import isStringHTML
from MaKaC.i18n import _

class WPSubContributionBase( WPMainBase, WPConferenceBase ):

    def __init__( self, rh, subContribution ):
        self._subContrib = self._target = subContribution
        self._conf = self._target.getConference()
        self._contrib = self._subContrib.getOwner()
        WPConferenceBase.__init__( self, rh, self._conf )

#    def _createMenu( self ):
#        main.WPMainBase._createMenu( self )
#        c = self._target
#        self._newContOpt.setActionURL( urlHandlers.UHSubContributionCreation.getURL(c) )
#        if not c.canModify( self._getAW() ):
#            self._modifyContOpt.disable()
#        self._modifySubContOpt.setActionURL( urlHandlers.UHSubContributionModification.getURL( c ) )
#        self._detailsSubContOpt.setActionURL( urlHandlers.UHSubContributionDisplay.getURL( c ) )
#        self._currentSubContOpt.enable()
#        self._calendarSubContOpt.setActionURL( urlHandlers.UHSubCalendar.getURL( [c] ) )
#        self._overviewSubContOpt.setActionURL( urlHandlers.UHSubContributionOverview.getURL( c ) )


class WPSubContributionDefaultDisplayBase( WPConferenceDefaultDisplayBase, WPSubContributionBase ):

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._includeJSPackage('Management') + \
               self._includeJSPackage('MaterialEditor')

    def __init__( self, rh, contribution ):
        WPSubContributionBase.__init__( self, rh, contribution )




class WSubContributionDisplayBase(wcomponents.WTemplated):
    def __init__(self, aw, subContrib):
        self._aw = aw
        self._subContrib = subContrib

    def _getHTMLRow( self, title, body):
        if body.strip() == "":
            return ""
        str = """
                <tr>
                    <td align="right" valign="top" class="displayField" nowrap><b>%s:</b></td>
                    <td width="100%%">%s</td>
                </tr>"""%(title, body)
        return str

    def _getMaterialHTML(self):
        lm=[]
        paper=self._subContrib.getPaper()
        if paper is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="paper"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(paper))),
                quoteattr(str(materialFactories.PaperFactory().getIconURL())),
                self.htmlText(materialFactories.PaperFactory().getTitle())))
        slides=self._subContrib.getSlides()
        if slides is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="slide"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(slides))),
                quoteattr(str(materialFactories.SlidesFactory().getIconURL())),
                self.htmlText(materialFactories.SlidesFactory().getTitle())))
        poster=self._subContrib.getPoster()
        if poster is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="poster"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(poster))),
                quoteattr(str(materialFactories.PosterFactory().getIconURL())),
                self.htmlText(materialFactories.PosterFactory().getTitle())))
        video=self._subContrib.getVideo()
        if video is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="video"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(video))),
                quoteattr(str(materialFactories.VideoFactory().getIconURL())),
                self.htmlText(materialFactories.VideoFactory().getTitle())))
        iconURL=quoteattr(str(Config.getInstance().getSystemIconURL("material")))
        minutes=self._subContrib.getMinutes()
        if minutes is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="minutes"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(minutes))),
                quoteattr(str(materialFactories.MinutesFactory().getIconURL())),
                self.htmlText(materialFactories.MinutesFactory().getTitle())))
        iconURL=quoteattr(str(Config.getInstance().getSystemIconURL("material")))
        for material in self._subContrib.getMaterialList():
            url=urlHandlers.UHMaterialDisplay.getURL(material)
            lm.append("""<a href=%s><img src=%s border="0" alt=""> %s</a>"""%(
                quoteattr(str(url)),iconURL,self.htmlText(material.getTitle())))
        return self._getHTMLRow("Material","<br>".join(lm))

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self.htmlText(self._subContrib.getTitle())
        vars["description"]=self._subContrib.getDescription()
        vars["id"]= self.htmlText(self._subContrib.getId())
        vars["duration"] =self._subContrib.getDuration().strftime("%H:%M")
        vars["location"]="blah"
        loc=self._subContrib.getLocation()
        if loc is not None:
            vars["location"]="<i>%s</i>"%(self.htmlText(loc.getName()))
            if loc.getAddress() is not None and loc.getAddress()!="":
                vars["location"]="%s <pre>%s</pre>"%(vars["location"],loc.getAddress())
        room=self._subContrib.getRoom()
        if room is not None:
            roomLink=linking.RoomLinker().getHTMLLink(room,loc)
            vars["location"]= _("""%s<br><small> _("Room"):</small> %s""")%(\
                vars["location"],roomLink)
        vars["location"]=self._getHTMLRow( _("Place"),vars["location"])
        vars["material"]=self._getMaterialHTML()
        vars["inContrib"]=""
        if self._subContrib.getParent() is not None:
            url=urlHandlers.UHContributionDisplay.getURL(self._subContrib.getParent())
            ContribCaption="%s"%self._subContrib.getParent().getTitle()
            vars["inContrib"]="""<a href=%s>%s</a>"""%(\
                quoteattr(str(url)),self.htmlText(ContribCaption))
        vars["inContrib"]=self._getHTMLRow( _("Included in contribution"),vars["inContrib"])
        l=[]
        for speaker in self._subContrib.getSpeakerList():
            l.append(self.htmlText(speaker.getFullName()))
        vars["speakers"]=self._getHTMLRow( _("Presenters"),"<br>".join(l))
        vars["modifyItem"]=""
        if self._subContrib.canModify( self._aw ):
            url=urlHandlers.UHSubContributionModification.getURL(self._subContrib)
            iconURL=Config.getInstance().getSystemIconURL("modify")
            vars["modifyItem"]="""<a href=%s><img src=%s border="0" alt="Jump to the modification interface"></a> """%(quoteattr(str(url)),quoteattr(str(iconURL)))
        return vars

class WSubContributionDisplayFull(WSubContributionDisplayBase):
    pass

class WSubContributionDisplayMin(WSubContributionDisplayBase):
    pass

class WSubContributionDisplay:
    def __init__(self, aw, subContrib):
        self._aw=aw
        self._subContrib=subContrib

    def getHTML(self, params={}):
        if self._subContrib.canAccess( self._aw ):
            c = WSubContributionDisplayFull( self._aw, self._subContrib)
            return c.getHTML( params )
        if self._subContrib.canView( self._aw ):
            c = WSubContributionDisplayMin( self._aw, self._subContrib)
            return c.getHTML( params )
        return ""

class WPSubContributionDisplay(WPSubContributionDefaultDisplayBase):
    navigationEntry=navigation.NESubContributionDisplay

    def _getBody(self, params):
        wc=WSubContributionDisplay(self._getAW(),self._subContrib)
        return wc.getHTML()



##nessa##

class WSubContributionDisplayBase(wcomponents.WTemplated):
    def __init__(self, aw, subContrib):
        self._aw = aw
        self._subContrib = subContrib

    def _getHTMLRow( self, title, body):
        if body.strip() == "":
            return ""
        str = """
                <tr>
                    <td align="right" valign="top" class="displayField" nowrap><b>%s:</b></td>
                    <td width="100%%">%s</td>
                </tr>"""%(title, body)
        return str

    def _getMaterialHTML(self):
        lm=[]
        paper=self._subContrib.getPaper()
        if paper is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="paper"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(paper))),
                quoteattr(str(materialFactories.PaperFactory().getIconURL())),
                self.htmlText(materialFactories.PaperFactory().getTitle())))
        slides=self._subContrib.getSlides()
        if slides is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="slide"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(slides))),
                quoteattr(str(materialFactories.SlidesFactory().getIconURL())),
                self.htmlText(materialFactories.SlidesFactory().getTitle())))
        poster=self._subContrib.getPoster()
        if poster is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="poster"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(poster))),
                quoteattr(str(materialFactories.PosterFactory().getIconURL())),
                self.htmlText(materialFactories.PosterFactory().getTitle())))
        video=self._subContrib.getVideo()
        if video is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="video"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(video))),
                quoteattr(str(materialFactories.VideoFactory().getIconURL())),
                self.htmlText(materialFactories.VideoFactory().getTitle())))
        iconURL=quoteattr(str(Config.getInstance().getSystemIconURL("material")))
        minutes=self._subContrib.getMinutes()
        if minutes is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="minutes"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(minutes))),
                quoteattr(str(materialFactories.MinutesFactory().getIconURL())),
                self.htmlText(materialFactories.MinutesFactory().getTitle())))
        iconURL=quoteattr(str(Config.getInstance().getSystemIconURL("material")))
        for material in self._subContrib.getMaterialList():
            url=urlHandlers.UHMaterialDisplay.getURL(material)
            lm.append("""<a href=%s><img src=%s border="0" alt=""> %s</a>"""%(
                quoteattr(str(url)),iconURL,self.htmlText(material.getTitle())))
        return self._getHTMLRow("Material","<br>".join(lm))

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self.htmlText(self._subContrib.getTitle())
        vars["description"]=self._subContrib.getDescription()
        vars["id"]= self.htmlText(self._subContrib.getId())
        vars["duration"] =(datetime(1900,1,1)+self._subContrib.getDuration()).strftime("%H:%M")
        vars["location"]="blah"
        loc=self._subContrib.getLocation()
        if loc is not None:
            vars["location"]="<i>%s</i>"%(self.htmlText(loc.getName()))
            if loc.getAddress() is not None and loc.getAddress()!="":
                vars["location"]="%s <pre>%s</pre>"%(vars["location"],loc.getAddress())
        room=self._subContrib.getRoom()
        if room is not None:
            roomLink=linking.RoomLinker().getHTMLLink(room,loc)
            vars["location"]= _("""%s<br><small> _("Room"):</small> %s""")%(\
                vars["location"],roomLink)
        vars["location"]=self._getHTMLRow( _("Place"),vars["location"])
        vars["material"]=self._getMaterialHTML()
        vars["inContrib"]=""
        if self._subContrib.getParent() is not None:
            url=urlHandlers.UHContributionDisplay.getURL(self._subContrib.getParent())
            ContribCaption="%s"%self._subContrib.getParent().getTitle()
            vars["inContrib"]="""<a href=%s>%s</a>"""%(\
                quoteattr(str(url)),self.htmlText(ContribCaption))
        vars["inContrib"]=self._getHTMLRow( _("Included in contribution"),vars["inContrib"])
        l=[]
        for speaker in self._subContrib.getSpeakerList():
            l.append(self.htmlText(speaker.getFullName()))
        vars["speakers"]=self._getHTMLRow( _("Presenters"),"<br>".join(l))
        return vars

class WSubContributionDisplayFull(WSubContributionDisplayBase):
    pass

class WSubContributionDisplayMin(WSubContributionDisplayBase):
    pass

class WSubContributionDisplay:
    def __init__(self, aw, subContrib):
        self._aw=aw
        self._subContrib=subContrib

    def getHTML(self, params={}):
        if self._subContrib.canAccess( self._aw ):
            c = WSubContributionDisplayFull( self._aw, self._subContrib)
            return c.getHTML( params )
        if self._subContrib.canView( self._aw ):
            c = WSubContributionDisplayMin( self._aw, self._subContrib)
            return c.getHTML( params )
        return ""

class WPSubContributionDisplay(WPSubContributionDefaultDisplayBase):
    navigationEntry=navigation.NESubContributionDisplay
    def _defineToolBar(self):
        edit=wcomponents.WTBItem( _("manage this contribution"),
            icon=Config.getInstance().getSystemIconURL("modify"),
            actionURL=urlHandlers.UHSubContributionModification.getURL(self._subContrib),
            enabled=self._target.canModify(self._getAW()))
        self._toolBar.addItem(edit)

    def _getBody(self, params):
        wc=WSubContributionDisplay(self._getAW(),self._subContrib)
        return wc.getHTML()



##
class WPSubContributionModifBase( WPConferenceModifBase ):

    def __init__( self, rh, subContribution ):
        WPConferenceModifBase.__init__( self, rh, subContribution.getConference() )
        self._subContrib = self._target = subContribution
        self._conf = self._target.getConference()
        self._contrib = self._subContrib.getOwner()

    def _getNavigationDrawer(self):
        pars = {"target": self._subContrib, "isModif": True}
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHSubContributionModification.getURL( self._target ) )
        #self._tabMaterials = self._tabCtrl.newTab( "materials", _("Files"), \
        self._tabMaterials = self._tabCtrl.newTab( "materials", _("Material"), \
                urlHandlers.UHSubContribModifMaterials.getURL( self._target ) )
        self._tabTools = self._tabCtrl.newTab( "tools", _("Tools"), \
                urlHandlers.UHSubContribModifTools.getURL( self._target ) )
        self._setActiveTab()

    def _getPageContent( self, params ):
        self._createTabCtrl()

        banner = wcomponents.WTimetableBannerModif(self._getAW(), self._target).getHTML()
        body = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )

        return banner + body

    def _setActiveSideMenuItem(self):
        if self._contrib.isScheduled():
            self._timetableMenuItem.setActive(True)
        else:
            self._contribListMenuItem.setActive(True)

    def _getTabContent( self, params ):
        return "nothing"


class WPSubContribModifMain( WPSubContributionModifBase ):

    def _setActiveTab( self ):
        self._tabMain.setActive()


class WSubContribModifTool(wcomponents.WTemplated):

    def __init__( self, subContrib ):
        self._subContrib = subContrib

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["deleteIconURL"] = Config.getInstance().getSystemIconURL("delete")
        vars["writeIconURL"] = Config.getInstance().getSystemIconURL("write_minutes")
        return vars


class WPSubContributionModifTools( WPSubContributionModifBase ):

    def _setActiveTab( self ):
        self._tabTools.setActive()

    def _getTabContent( self, params ):
        wc = WSubContribModifTool( self._target )
        pars = { \
"deleteSubContributionURL": urlHandlers.UHSubContributionDelete.getURL( self._target ), \
"writeMinutes": urlHandlers.UHSubContributionWriteMinutes.getURL( self._target ) }
        return wc.getHTML( pars )


class WPSubContributionModifMaterials( WPSubContributionModifBase ):
    #TODO: maybe join it with contributions.WPContributionModifMaterials

    _userData = ['favorite-user-list']

    def __init__(self, rh, subcontribution):
        WPSubContributionModifBase.__init__(self, rh, subcontribution)

    def _setActiveTab( self ):
        self._tabMaterials.setActive()

    def _getTabContent( self, pars ):
        wc=wcomponents.WShowExistingMaterial(self._target)
        #pars["materialTypes"] = self._matTypes
        return wc.getHTML()


class WSubContribModNewSpeaker(wcomponents.WTemplated):

    def __init__(self,subcontrib):
        self._subcontrib = subcontrib

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHSubContributionNewSpeaker.getURL(self._subcontrib)))
        vars["titles"]=TitlesRegistry().getSelectItemsHTML()
        return vars

class WPSubModNewSpeaker( WPSubContribModifMain ):

    def _getTabContent( self, params ):
        wc = WSubContribModNewSpeaker(self._subContrib)
        return wc.getHTML( params )



class WPSubContributionModification( WPSubContribModifMain ):
    def _getTabContent( self, params ):
        wc = WSubContribModifMain( self._target, materialFactories.ContribMFRegistry() )
        place = ""
        if self._target.getLocation() is not None:
            place = self._target.getLocation().getName()
        pars = { "dataModificationURL": urlHandlers.UHSubContributionDataModification.getURL( self._target ), \
                "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
                "deleteSubContribURL": urlHandlers.UHSubContributionDelete.getURL, \
                "writeMinutesURL": urlHandlers.UHSubContributionWriteMinutes.getURL, \
                "place": place, \
                "duration": (datetime(1900,1,1)+self._target.getDuration()).strftime("%Hh%M'"), \
                "confId": self._target.getConference().getId(), \
                "contribId": self._target.getOwner().getId(), \
                "subContribId": self._target.getId(), \
                "addMaterialURL": str(urlHandlers.UHSubContributionAddMaterial.getURL( self._target )), \
                "removeMaterialsURL": str(urlHandlers.UHSubContributionRemoveMaterials.getURL()), \
                "modifyMaterialURLGen": urlHandlers.UHMaterialModification.getURL, \
                "searchSpeakersURL": quoteattr(str(urlHandlers.UHSubContributionSelectSpeakers.getURL(self._target))), \
                "removeSpeakersURL": quoteattr(str(urlHandlers.UHSubContributionRemoveSpeakers.getURL(self._target))),\
                "modSpeakerURLGen":urlHandlers.UHSubContribModPresenter.getURL,\
                "newSpeakerURL": quoteattr(str(urlHandlers.UHSubContributionNewSpeaker.getURL(self._target)))}
        return wc.getHTML( pars )

class WSubContributionDataModification(wcomponents.WTemplated):

    def __init__( self, subContribution ):
        self.__subContrib = subContribution
        self.__owner = self.__subContrib.getOwner()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self.__subContrib.getTitle()
        vars["description"] = self.__subContrib.getDescription()
        vars["keywords"] = self.__subContrib.getKeywords()
        vars["durationHours"] = (datetime(1900,1,1)+self.__subContrib.getDuration()).hour
        vars["durationMinutes"] = (datetime(1900,1,1)+self.__subContrib.getDuration()).minute
        vars["locator"] = self.__subContrib.getLocator().getWebForm()
        vars["speakers"] = self.__subContrib.getSpeakerText()
        return vars


class WPSubContribData( WPSubContribModifMain ):

    def _getTabContent( self, params ):
        wc = WSubContributionDataModification(self._target)
        params["postURL"] = urlHandlers.UHSubContributionDataModif.getURL()
        return wc.getHTML( params )


class WPSubContribSelectSpeakers( WPSubContribModifMain ):
    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WAuthorSearch( self._conf, urlHandlers.UHSubContributionSelectSpeakers.getURL(),forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHSubContributionAddSpeakers.getURL()
        return wc.getHTML( params )


class WPSubContribAddMaterial( WPSubContribModifMain ):

    def __init__( self, rh, contrib, mf ):
        WPSubContribModifMain.__init__( self, rh, contrib )
        self._mf = mf

    def _getTabContent( self, params ):
        if self._mf:
            comp = self._mf.getCreationWC( self._target )
        else:
            comp = wcomponents.WMaterialCreation( self._target )
        pars = { "postURL": urlHandlers.UHSubContributionPerformAddMaterial.getURL() }
        return comp.getHTML( pars )

class WSubContributionDeletion(object):

    def __init__( self, subContribList ):
        self._subContribList = subContribList

    def getHTML( self, actionURL ):
        l = []
        for subContrib in self._subContribList:
            l.append("""<li><i>%s</i></li>"""%subContrib.getTitle())
        msg =  _("""
        <font size="+2">Are you sure that you want to <font color="red"><b>DELETE</b></font> the following sub contributions:<ul>%s</ul>?</font><br>
              """)%("".join(l))
        wc = wcomponents.WConfirmation()
        subContribIdList = []
        for subContrib in self._subContribList:
            subContribIdList.append( subContrib.getId() )
        return wc.getHTML( msg, actionURL, {"selectedCateg": subContribIdList}, \
                                            confirmButtonCaption= _("Yes"), \
                                            cancelButtonCaption= _("No") )


class WPSubContributionDeletion( WPSubContributionModifTools ):

    def _getTabContent( self, params ):
        wc = WSubContributionDeletion( [self._target] )
        return wc.getHTML( urlHandlers.UHSubContributionDelete.getURL( self._target ) )

class WSubContribModPresenter(wcomponents.WTemplated):

    def __init__(self,auth):
        self._auth=auth

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHSubContribModPresenter.getURL(self._auth)))
        vars["titles"]=TitlesRegistry.getSelectItemsHTML(self._auth.getTitle())
        vars["surName"]=quoteattr(self._auth.getFamilyName())
        vars["name"]=quoteattr(self._auth.getFirstName())
        vars["affiliation"]=quoteattr(self._auth.getAffiliation())
        vars["email"]=quoteattr(self._auth.getEmail())
        vars["address"]=self._auth.getAddress()
        vars["phone"]=quoteattr(self._auth.getPhone())
        vars["fax"]=quoteattr(self._auth.getFax())
        return vars

class WPModPresenter( WPSubContribModifMain ):

    def _getTabContent( self, params ):
        wc = WSubContribModPresenter(params["author"])
        return wc.getHTML()

class WSubContribSpeakerTable(wcomponents.WTemplated):

    def __init__(self, authList, subContrib):
        self._list = authList
        self._conf = subContrib.getConference()
        self._subContrib = subContrib

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        urlGen=vars.get("modSpeakerURLGen",None)
        l = []
        for author in self._list:
            authCaption=author.getFullName()
            if author.getAffiliation()!="":
                authCaption="%s (%s)"%(authCaption,author.getAffiliation())
            if urlGen:
                authCaption="""<a href=%s>%s</a>"""%(urlGen(author),self.htmlText(authCaption))
            href ="\"\""
            if author.getEmail() != "":
                mailtoSubject =  _("""[%s]  _("Sub-Contribution") %s: %s""")%( self._conf.getTitle(), self._subContrib.getId(), self._subContrib.getTitle() )
                mailtoURL = "mailto:%s?subject=%s"%( author.getEmail(), urllib.quote( mailtoSubject ) )
                href = quoteattr( mailtoURL )
            emailHtml = """ <a href=%s><img src="%s" style="border:0px" alt="email"></a> """%(href, Config.getInstance().getSystemIconURL("smallEmail"))
            l.append("""<input type="checkbox" name="selAuthor" value=%s>%s %s"""%(quoteattr(author.getId()),emailHtml,authCaption))
        vars["authors"] = "<br>".join(l)
        return vars

class WSubContribModifMain(wcomponents.WTemplated):

    def __init__( self, subContribution, mfRegistry ):
        self._subContrib = subContribution
        self._mfRegistry = mfRegistry

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["locator"] = self._subContrib.getLocator().getWebForm()
        vars["title"] = self._subContrib.getTitle()
        if isStringHTML(self._subContrib.getDescription()):
            vars["description"] = self._subContrib.getDescription()
        else:
            vars["description"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._subContrib.getDescription()
        vars["dataModifButton"] = ""
        vars["dataModifButton"] =  _("""<input type="submit" class="btn" value="_("modify")">""")
        speakerText = self._subContrib.getSpeakerText()
        if speakerText != "":
            speakerText = "%s<br>"%speakerText
        p = {"newSpeakerURL":vars["newSpeakerURL"],\
            "searchSpeakersURL":vars["searchSpeakersURL"], \
            "removeSpeakersURL":vars["removeSpeakersURL"], \
            "modSpeakerURLGen":vars['modSpeakerURLGen']}
        pt = WSubContribSpeakerTable(self._subContrib.getSpeakerList(), self._subContrib).getHTML(p)
        vars["speakersTable"] = "%s%s"%(speakerText, pt)
        vars["reportNumbersTable"]=wcomponents.WReportNumbersTable(self._subContrib,"subcontribution").getHTML()
        vars["keywords"] = self._subContrib.getKeywords()
        return vars

class WPSubContributionWriteMinutes( WPSubContributionModifTools ):

    def _getTabContent( self, params ):
        wc = wcomponents.WWriteMinutes( self._target )
        pars = {"postURL": urlHandlers.UHSubContributionWriteMinutes.getURL(self._target) }
        return wc.getHTML( pars )

class WPSubContributionDisplayWriteMinutes( WPSubContributionDefaultDisplayBase ):
    navigationEntry=navigation.NESubContributionDisplay

    def _getBody( self, params ):
        wc = wcomponents.WWriteMinutes( self._target )
        pars = {"postURL": urlHandlers.UHSubContributionDisplayWriteMinutes.getURL(self._target) }
        return wc.getHTML( pars )

class WPSubContributionReportNumberEdit(WPSubContributionModifBase):

    def __init__(self, rh, subcontribution, reportNumberSystem):
        WPSubContributionModifBase.__init__(self, rh, subcontribution)
        self._reportNumberSystem=reportNumberSystem

    def _setActiveTab( self ):
        #self._innerTabMain.setActive()
        pass


    def _getTabContent( self, params):
        wc=wcomponents.WModifReportNumberEdit(self._target, self._reportNumberSystem, "subcontribution")
        return wc.getHTML(params)
