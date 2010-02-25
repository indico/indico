# -*- coding: utf-8 -*-
##
## $Id: contributions.py,v 1.112 2009/06/17 16:38:52 pferreir Exp $
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
from xml.sax.saxutils import quoteattr
from datetime import datetime
import MaKaC.conference as conference
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.linking as linking
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.navigation as navigation
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.webinterface.timetable as timetable
from MaKaC.webinterface.pages.conferences import WPConfModifScheduleGraphic, WPConferenceBase, WPConferenceModifBase, WPConferenceDefaultDisplayBase
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.common import Config
from MaKaC.common.utils import isStringHTML, formatDateTime
from MaKaC.common import info
from MaKaC.i18n import _
from MaKaC import user
from pytz import timezone
import MaKaC.common.timezoneUtils as timezoneUtils


class WPContributionBase( WPMainBase, WPConferenceBase ):

    def __init__( self, rh, contribution ):
        self._contrib = self._target = contribution
        WPConferenceBase.__init__( self, rh, self._contrib.getConference() )
        self._navigationTarget = contribution


class WPContributionDefaultDisplayBase( WPConferenceDefaultDisplayBase, WPContributionBase ):

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._includeJSPackage('Management') + \
               self._includeJSPackage('MaterialEditor')

    def __init__( self, rh, contribution ):
        WPContributionBase.__init__( self, rh, contribution )


class WContributionDisplayBase(wcomponents.WTemplated):

    def __init__(self, aw, contrib):
        self._aw = aw
        self._contrib = contrib

    def _getHTMLRow( self, title, body):
        if body.strip() == "":
            return ""
        str = """
                <tr>
                    <td align="right" valign="top" class="displayField" nowrap><b>%s:</b></td>
                    <td width="100%%" valign="top">%s</td>
                </tr>"""%(title, body)
        return str

    def _getAdditionalFieldsHTML(self):
        html=""
        afm = self._contrib.getConference().getAbstractMgr().getAbstractFieldsMgr()
        for f in afm.getActiveFields():
            id = f.getId()
            caption = f.getName()
            html+=self._getHTMLRow(caption, self._contrib.getField(id))
        return html

    def _getSubContributionItem(self, sc, modifURL):
        modifyItem = ""
        url = urlHandlers.UHSubContributionDisplay.getURL(sc)
        if sc.canModify( self._aw ):
            modifyItem = _("""
                          <a href="%s"><img src="%s" border="0" alt='_("Jump to the modification interface")'></a>
                         """)%(modifURL, Config.getInstance().getSystemIconURL( "modify" ) )
        return """
                <tr>
                <td valign="middle">
                            %s<b>&nbsp;<a href=%s>%s</a></b>
                        </td>
                </tr>
               """%(modifyItem, quoteattr(str(url)), sc.getTitle())

    def _getWithdrawnNoticeHTML(self):
        res=""
        if isinstance(self._contrib.getCurrentStatus(),conference.ContribStatusWithdrawn):
            res= _("""
                <tr>
                    <td colspan="2" align="center"><b>--_("WITHDRAWN")--</b></td>
                </tr>
                """)
        return res

    def _getSubmitButtonHTML(self):
        res=""
        status=self._contrib.getCurrentStatus()
        if not isinstance(status,conference.ContribStatusWithdrawn) and \
                            self._contrib.canUserSubmit(self._aw.getUser()):
            res= _("""<input type="submit" class="btn" value="_("manage material")">""")
        return res

    def _getModifIconHTML(self):
        res=""
        if self._contrib.canModify(self._aw):
            res="""<a href="%s"><img src="%s" border="0" alt="Jump to the modification interface"></a>""" % (urlHandlers.UHContributionModification.getURL(self._contrib), Config.getInstance().getSystemIconURL( "modify" ))
        return res

    def _getSubmitIconHTML(self):
        res=""
        if self._contrib.canUserSubmit(self._aw.getUser()):
            res="""<a href="%s"><img src="%s" border="0" alt="Upload files"></a>""" % ('FIXME', Config.getInstance().getSystemIconURL( "submit" ))
        return res

    def _getMaterialHTML(self):
        lm=[]
        paper=self._contrib.getPaper()
        if paper is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="paper"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(paper))),
                quoteattr(str(materialFactories.PaperFactory().getIconURL())),
                self.htmlText(materialFactories.PaperFactory().getTitle())) )
        slides=self._contrib.getSlides()
        if slides is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="slide"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(slides))),
                quoteattr(str(materialFactories.SlidesFactory().getIconURL())),
                self.htmlText(materialFactories.SlidesFactory().getTitle())))
        poster=self._contrib.getPoster()
        if poster is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="poster"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(poster))),
                quoteattr(str(materialFactories.PosterFactory().getIconURL())),
                self.htmlText(materialFactories.PosterFactory().getTitle())))
        video=self._contrib.getVideo()
        if video is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="video"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(video))),
                quoteattr(str(materialFactories.VideoFactory().getIconURL())),
                self.htmlText(materialFactories.VideoFactory().getTitle())))
        iconURL=quoteattr(str(Config.getInstance().getSystemIconURL("material")))
        minutes=self._contrib.getMinutes()
        if minutes is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="minutes"> %s</a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(minutes))),
                quoteattr(str(materialFactories.MinutesFactory().getIconURL())),
                self.htmlText(materialFactories.MinutesFactory().getTitle())))
        iconURL=quoteattr(str(Config.getInstance().getSystemIconURL("material")))
        for material in self._contrib.getMaterialList():
            url=urlHandlers.UHMaterialDisplay.getURL(material)
            lm.append("""<a href=%s><img src=%s border="0" alt=""> %s</a>"""%(
                quoteattr(str(url)),iconURL,self.htmlText(material.getTitle())))
        return self._getHTMLRow("Material","<br>".join(lm))

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["contribXML"]=quoteattr(str(urlHandlers.UHContribToXML.getURL(self._contrib)))
        vars["contribPDF"]=quoteattr(str(urlHandlers.UHContribToPDF.getURL(self._contrib)))
        vars["contribiCal"]=quoteattr(str(urlHandlers.UHContribToiCal.getURL(self._contrib)))
        vars["xmlIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("xml")))
        vars["printIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("pdf")))
        vars["icalIconURL"]=quoteattr(str(Config.getInstance().getSystemIconURL("ical")))

        vars["title"] = self.htmlText(self._contrib.getTitle())
        if isStringHTML(self._contrib.getDescription()):
            vars["description"] = self._contrib.getDescription()
        else:
            vars["description"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._contrib.getDescription()
        vars["additionalFields"] = self._getAdditionalFieldsHTML()
        vars["id"]=self.htmlText(self._contrib.getId())
        vars["startDate"] = _("""--_("not yet scheduled")--""")
        vars["startTime"] = ""
        if self._contrib.isScheduled():
            tzUtil = timezoneUtils.DisplayTZ(self._aw,self._contrib.getOwner())
            tz = tzUtil.getDisplayTZ()
            sDate = self._contrib.getStartDate().astimezone(timezone(tz))
            vars["startDate"]=self.htmlText(sDate.strftime("%d-%b-%Y"))
            vars["startTime"]=self.htmlText(sDate.strftime("%H:%M") + " (" + tz + ")")
        vars["location"]=""
        loc=self._contrib.getLocation()
        if loc is not None:
            vars["location"]="<i>%s</i>"%(self.htmlText(loc.getName()))
            if loc.getAddress() is not None and loc.getAddress()!="":
                vars["location"]="%s <pre>%s</pre>"%(vars["location"],loc.getAddress())
        room=self._contrib.getRoom()
        if room is not None:
            roomLink=linking.RoomLinker().getHTMLLink(room,loc)
            vars["location"]= _("""%s<br><small> _("Room"):</small> %s""")%(\
                vars["location"],roomLink)
            if self._contrib.getBoardNumber()!="":
                vars["location"]= _("""%s - _("board #"): %s""")%(vars["location"],self._contrib.getBoardNumber())
        else:
            if self._contrib.getBoardNumber()!="":
                vars["location"]= _("""%s <br> _("board #"): %s""")%(vars["location"],self._contrib.getBoardNumber())

        vars["location"]=self._getHTMLRow( _("Place"),vars["location"])

        authIndex = self._contrib.getConference().getAuthorIndex()

        l=[]
        for speaker in self._contrib.getSpeakerList():
            l.append(self.htmlText(speaker.getFullName()))
        vars["speakers"]=self._getHTMLRow( _("Presenters"),"<br>".join(l))

        pal = []
        for pa in self._contrib.getPrimaryAuthorList():
            authURL=urlHandlers.UHContribAuthorDisplay.getURL(self._contrib.getConference())
            authURL.addParam("authorId", authIndex._getKey(pa))
            authCaption="<a href=%s>%s</a>"%(quoteattr(str(authURL)), self.htmlText(pa.getFullName()))
            if pa.getAffiliation()!="":
                authCaption="%s (%s)"%(authCaption,self.htmlText(pa.getAffiliation()))
            pal.append(authCaption)
        vars["primaryAuthors"]=self._getHTMLRow( _("Primary Authors"),"<br>".join(pal))
        cal = []
        for ca in self._contrib.getCoAuthorList():
            authCaption="%s"%ca.getFullName()
            if ca.getAffiliation()!="":
                authCaption="%s (%s)"%(authCaption,ca.getAffiliation())
            cal.append(self.htmlText(authCaption))
        vars["coAuthors"]=self._getHTMLRow( _("Co-Authors"),"<br>".join(cal))
        vars["contribType"]=""
        if self._contrib.getType() != None:
            vars["contribType"]=self._getHTMLRow( _("Contribution type"),self.htmlText(self._contrib.getType().getName()))

        #TODO: fuse this two lines into one, so that they are not both executed...
        #but the 1st line generates a lot of HTML in Python...
        vars["material"]=self._getMaterialHTML()

        from MaKaC.webinterface.rh.conferenceBase import RHSubmitMaterialBase
        vars["MaterialList"] = wcomponents.WShowExistingMaterial(self._contrib).getHTML()

        vars["duration"]=""
        if self._contrib.getDuration() is not None:
            vars["duration"]=(datetime(1900,1,1)+self._contrib.getDuration()).strftime("%M'")
            if (datetime(1900,1,1)+self._contrib.getDuration()).hour>0:
                vars["duration"]=(datetime(1900,1,1)+self._contrib.getDuration()).strftime("%Hh%M'")
        vars["inSession"]=""
        if self._contrib.getSession() is not None:
            url=urlHandlers.UHSessionDisplay.getURL(self._contrib.getSession())
            sessionCaption="%s"%self._contrib.getSession().getTitle()
            vars["inSession"]="""<a href=%s>%s</a>"""%(\
                quoteattr(str(url)),self.htmlText(sessionCaption))
        vars["inSession"]=self._getHTMLRow( _("Included in session"),vars["inSession"])
        vars["inTrack"]=""
        if self._contrib.getTrack():
            trackCaption=self._contrib.getTrack().getTitle()
            vars["inTrack"]="""%s"""%(self.htmlText(trackCaption))
        vars["inTrack"]=self._getHTMLRow( _("Included in track"),vars["inTrack"])
        scl = []
        for sc in self._contrib.getSubContributionList():
            url=urlHandlers.UHSubContributionModification.getURL(sc)
            scl.append(self._getSubContributionItem(sc,url))
        vars["subConts"]=""
        if scl:
            scl.insert(0,"""<table align="left" valign="top" width="100%%" border="0" cellpadding="3" cellspacing="3">""")
            scl.append("</table>")
            vars["subConts"]=self._getHTMLRow( _("Sub-contributions"),"".join(scl))
        vars["withdrawnNotice"]=self._getWithdrawnNoticeHTML()
        vars["submitBtn"]=self._getSubmitButtonHTML()
        vars["submitURL"]=quoteattr('FIXME')
        vars["modifIcon"] = self._getModifIconHTML()
        vars["submitIcon"] = self._getSubmitIconHTML()
        vars["Contribution"] = self._contrib
        import contributionReviewing
        vars["reviewingStuffDisplay"]= contributionReviewing.WContributionReviewingDisplay(self._contrib).getHTML({"ShowReviewingTeam" : False})
        vars["reviewingHistoryStuffDisplay"]= contributionReviewing.WContributionReviewingHistory(self._contrib).getHTML({"ShowReviewingTeam" : False})
        return vars


class WContributionDisplayFull(WContributionDisplayBase):
    pass


class WContributionDisplayMin(WContributionDisplayBase):
    pass


class WContributionDisplay:

    def __init__(self, aw, contrib):
        self._aw = aw
        self._contrib = contrib

    def getHTML(self,params={}):
        if self._contrib.canAccess( self._aw ):
            c = WContributionDisplayFull( self._aw, self._contrib)
            return c.getHTML( params )
        if self._contrib.canView( self._aw ):
            c = WContributionDisplayMin( self._aw, self._contrib)
            return c.getHTML( params )
        return ""


class WPContributionDisplay( WPContributionDefaultDisplayBase ):
    navigationEntry = navigation.NEContributionDisplay

    def _defineToolBar(self):
        edit=wcomponents.WTBItem( _("manage this contribution"),
            icon=Config.getInstance().getSystemIconURL("modify"),
            actionURL=urlHandlers.UHContributionModification.getURL(self._contrib),
            enabled=self._target.canModify(self._getAW()))
        pdf=wcomponents.WTBItem( _("get PDF of this contribution"),
            icon=Config.getInstance().getSystemIconURL("pdf"),
            actionURL=urlHandlers.UHContribToPDF.getURL(self._contrib))
        xml=wcomponents.WTBItem( _("get XML of this contribution"),
            icon=Config.getInstance().getSystemIconURL("xml"),
            actionURL=urlHandlers.UHContribToXML.getURL(self._contrib))
        ical=wcomponents.WTBItem( _("get ICal of this contribution"),
            icon=Config.getInstance().getSystemIconURL("ical"),
            actionURL=urlHandlers.UHContribToiCal.getURL(self._contrib))
        self._toolBar.addItem(edit)
        self._toolBar.addItem(pdf)
        self._toolBar.addItem(xml)
        self._toolBar.addItem(ical)

    def _getBody( self, params ):
        wc=WContributionDisplay( self._getAW(), self._contrib )
        return wc.getHTML()



class WPContributionModifBase( WPConferenceModifBase  ):

    def __init__( self, rh, contribution ):
        WPConferenceModifBase.__init__( self, rh, contribution.getConference() )
        self._contrib = self._target = contribution

    def _getEnabledControls(self):
        return False

    def _getNavigationDrawer(self):
        pars = {"target": self._contrib , "isModif": True}
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _createTabCtrl( self ):

        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHContributionModification.getURL( self._target ) )
        self._tabMaterials = self._tabCtrl.newTab( "materials", _("Material"), \
                urlHandlers.UHContribModifMaterials.getURL( self._target ) )
        #self._tabMaterials = self._tabCtrl.newTab( "materials", _("Files"), \
        #        urlHandlers.UHContribModifMaterials.getURL( self._target ) )
        self._tabSubCont = self._tabCtrl.newTab( "subCont", _("Sub Contribution"), \
                urlHandlers.UHContribModifSubCont.getURL( self._target ) )
        self._tabAC = self._tabCtrl.newTab( "ac", _("Protection"), \
                urlHandlers.UHContribModifAC.getURL( self._target ) )
        self._tabTools = self._tabCtrl.newTab( "tools", _("Tools"), \
                urlHandlers.UHContribModifTools.getURL( self._target ) )

        hasReviewingEnabled = self._contrib.getConference().hasEnabledSection('paperReviewing')
        confReviewChoice = self._contrib.getConference().getConfReview().getChoice()

        if hasReviewingEnabled and confReviewChoice != 1:

            self._tabReviewing = self._tabCtrl.newTab( "reviewing", "Reviewing", \
                urlHandlers.UHContributionModifReviewing.getURL( self._target ) )

            if (confReviewChoice == 3 or confReviewChoice == 4) and \
                self._contrib.getReviewManager().isEditor(self._rh._getUser()) and \
                (not self._contrib.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() or self._conf.getConfReview().getChoice() == 3) and \
                self._contrib.getReviewManager().getLastReview().isAuthorSubmitted():

                self._tabJudgeEditing = self._tabCtrl.newTab( "editing", "Editing", \
                                         urlHandlers.UHContributionEditingJudgement.getURL(self._target) )

            if (confReviewChoice == 2 or confReviewChoice == 4) and \
                self._contrib.getReviewManager().isReviewer(self._rh._getUser()) and \
                not self._contrib.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted() and \
                self._contrib.getReviewManager().getLastReview().isAuthorSubmitted():

                self._tabGiveAdvice = self._tabCtrl.newTab( "advice", "Advice on reviewing", \
                                      urlHandlers.UHContributionGiveAdvice.getURL(self._target))

            if len(self._contrib.getReviewManager().getVersioning()) > 1 or self._contrib.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted():
                self._tabReviewingHistory = self._tabCtrl.newTab( "reviewing_history", "Reviewing History", \
                                            urlHandlers.UHContributionModifReviewingHistory.getURL( self._target ) )

        self._setActiveTab()
        self._setupTabCtrl()

    def _setActiveTab( self ):
        pass

    def _setupTabCtrl(self):
        pass

    def _setActiveSideMenuItem(self):
        if self._target.isScheduled():
            self._timetableMenuItem.setActive(True)
        else:
            self._contribListMenuItem.setActive(True)

    def _getPageContent( self, params ):
        self._createTabCtrl()
        #TODO: check if it comes from the timetable or the contribution list
        # temp solution: isScheduled.
        if self._target.isScheduled():
            banner = wcomponents.WTimetableBannerModif(self._target).getHTML()
        else:
            banner = wcomponents.WContribListBannerModif(self._target).getHTML()
        body = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner + body


class WPContribModifMain( WPContributionModifBase ):

    def _setActiveTab( self ):
        self._tabMain.setActive()

class WPContributionModifTools( WPContributionModifBase ):

    def _setActiveTab( self ):
        self._tabTools.setActive()

    def _getTabContent( self, params ):
        wc = wcomponents.WContribModifTool( self._target )
        pars = { \
"deleteContributionURL": urlHandlers.UHContributionDelete.getURL( self._target ), \
"MoveContributionURL": urlHandlers.UHContributionMove.getURL( self._target ), \
"writeMinutes": urlHandlers.UHContributionWriteMinutes.getURL( self._target ) }
        return wc.getHTML( pars )

class WPContributionModifMaterials( WPContributionModifBase ):
    def __init__(self, rh, contribution):
        WPContributionModifBase.__init__(self, rh, contribution)

    def _setActiveTab( self ):
        self._tabMaterials.setActive()

    def _getTabContent( self, pars ):
        wc=wcomponents.WShowExistingMaterial(self._target)
        return wc.getHTML( pars )

class WPModSearchPrimAuthor ( WPContribModifMain ):

    def _getTabContent(self,params):
        url = urlHandlers.UHContribModPrimAuthSearch.getURL()
        self._conf = self._target.getConference()
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc=wcomponents.WAuthorSearch(self._conf,url, addTo=2,forceWithoutExtAuth=searchLocal)
        params["addURL"]=urlHandlers.UHContribModPrimAuthSearchAdd.getURL()
        return wc.getHTML( params )

class WPModSearchCoAuthor ( WPContribModifMain ):

    def _getTabContent(self,params):
        url = urlHandlers.UHContribModCoAuthSearch.getURL()
        self._conf = self._target.getConference()
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc=wcomponents.WAuthorSearch(self._conf,url, addTo=2,forceWithoutExtAuth=searchLocal)
        params["addURL"]=urlHandlers.UHContribModCoAuthSearchAdd.getURL()
        return wc.getHTML( params )

class WPModSearchSpeaker ( WPContribModifMain ):

    def _getTabContent(self,params):
        url = urlHandlers.UHContribModSpeakerSearch.getURL()
        self._conf = self._target.getConference()
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc=wcomponents.WAuthorSearch(self._conf,url, addTo=2,forceWithoutExtAuth=searchLocal)
        params["addURL"]=urlHandlers.UHContribModSpeakerSearchAdd.getURL()
        return wc.getHTML( params )

class WAuthorTable(wcomponents.WTemplated):

    def __init__(self, authList, contrib):
        self._list = authList
        self._conf = contrib.getConference()
        self._contrib = contrib

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        urlGen=vars.get("modAuthorURLGen",None)
        l = []
        for author in self._list:
            authCaption=author.getFullName()
            if author.getAffiliation()!="":
                authCaption="%s (%s)"%(authCaption,author.getAffiliation())
            if urlGen:
                authCaption="""<a href=%s>%s</a>"""%(urlGen(author),self.htmlText(authCaption))
            href ="\"\""
            if author.getEmail() != "":
                mailtoSubject = """[%s] _("Contribution") %s: %s"""%( self._conf.getTitle(), self._contrib.getId(), self._contrib.getTitle() )
                mailtoURL = "mailto:%s?subject=%s"%( author.getEmail(), urllib.quote( mailtoSubject ) )
                href = quoteattr( mailtoURL )
            emailHtml = """ <a href=%s><img src="%s" style="border:0px" alt="email"></a> """%(href, Config.getInstance().getSystemIconURL("smallEmail"))
            upURLGen=vars.get("upAuthorURLGen",None)
            up=""
            if upURLGen is not None:
                up="""<a href=%s><img src=%s border="0" alt="up"></a>"""%(quoteattr(str(upURLGen(author))),quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))))
            downURLGen=vars.get("downAuthorURLGen",None)
            down=""
            if downURLGen is not None:
                down="""<a href=%s><img src=%s border="0" alt="down"></a>"""%(quoteattr(str(downURLGen(author))),quoteattr(str(Config.getInstance().getSystemIconURL("downArrow"))))
            l.append("""<input type="checkbox" name="selAuthor" value=%s>%s%s%s %s"""%(quoteattr(author.getId()),up,down,emailHtml,authCaption))
        vars["authors"] = "<br>".join(l)
        vars["remAuthorsURL"] = vars.get("remAuthorsURL","")
        vars["addAuthorsURL"] = vars.get("addAuthorsURL","")
        vars["searchAuthorURL"] = vars.get("searchAuthorURL","")
        return vars

class WContribModifClosed(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["closedIconURL"] = Config.getInstance().getSystemIconURL("closed")
        return vars

class WContribModifMain(wcomponents.WTemplated):

    def __init__( self, contribution, mfRegistry, eventType = "conference" ):
        self._contrib = contribution
        self._mfRegistry = mfRegistry
        self._eventType = eventType

    def _getAbstractHTML( self ):
        if not self._contrib.getConference().hasEnabledSection("cfa"):
            return ""
        abs = self._contrib.getAbstract()
        if abs is not None:
            html = _("""
             <tr>
                <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Abstract")</span></td>
                <td bgcolor="white" class="blacktext"><a href=%s>%s - %s</a></td>
            </tr>
            <tr>
                <td colspan="3" class="horizontalLine">&nbsp;</td>
            </tr>
                """)%( quoteattr(str(urlHandlers.UHAbstractManagment.getURL(abs))),\
                    self.htmlText(abs.getId()), abs.getTitle() )
        else:
            html = _("""
             <tr>
                <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Abstract")</span></td>
                <td bgcolor="white" class="blacktext">&nbsp;&nbsp;&nbsp;<font color="red"> _("The abstract associated with this contribution has been removed")</font></td>
            </tr>
            <tr>
                <td colspan="3" class="horizontalLine">&nbsp;</td>
            </tr>
                """)
        return html

    def _getSpeakersHTML(self):
        res=[]
        for spk in self._contrib.getSpeakerList():
            fullName = self.htmlText(spk.getFullName())
            submitter = ""
            if spk.getEmail() in self._contrib.getSubmitterEmailList():
                submitter = _(""" <small>(_("Submitter"))</small>""")
            for emails in [av.getEmails() for av in self._contrib.getSubmitterList() if av != None and hasattr(av,"getEmails")]:
                if spk.getEmail() in emails:
                    submitter = _(""" <small>( _("Submitter"))</small>""")
                    break

            #if not self._contrib.isAuthor(spk):
            fullName = """<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHContribModSpeaker.getURL(spk))), \
                                                self.htmlText(spk.getFullName()))
            res.append("""<input type="checkbox" name="selSpeaker" value=%s><i>%s</i>%s"""%(quoteattr(str(spk.getId())),fullName, submitter))
        return "<br>".join(res)

    def _getAuthorsForSpeakers(self):
        res=["""<option value=""></option>"""]
        for auth in self._contrib.getPrimaryAuthorList():
            if self._contrib.isSpeaker(auth):
                continue
            res.append("""<option value=%s>%s</option>"""%(quoteattr(auth.getId()),self.htmlText(auth.getFullName())))
        for auth in self._contrib.getCoAuthorList():
            if self._contrib.isSpeaker(auth):
                continue
            res.append("""<option value=%s>%s</option>"""%(quoteattr(auth.getId()),self.htmlText(auth.getFullName())))
        return "".join(res)

    def _getChangeTracksHTML(self):
        res=[]
        if not self._contrib.getTrack() is None:
            res=[ _("""<option value="">--_("none")--</option>""")]
        for track in self._contrib.getConference().getTrackList():
            if self._contrib.getTrack()==track:
                continue
            res.append("""<option value=%s>%s</option>"""%(quoteattr(str(track.getId())),self.htmlText(track.getTitle())))
        return "".join(res)

    def _getChangeSessionsHTML(self):
        res=[]
        if not self._contrib.getSession() is None:
            res=[ _("""<option value="">--_("none")--</option>""")]
        for session in self._contrib.getConference().getSessionListSorted():
            if self._contrib.getSession()==session:
                continue
            from MaKaC.common.TemplateExec import truncateTitle
            res.append("""<option value=%s>%s</option>"""%(quoteattr(str(session.getId())),self.htmlText(truncateTitle(session.getTitle(), 60))))
        return "".join(res)

    def _getWithdrawnNoticeHTML(self):
        res=""
        status=self._contrib.getCurrentStatus()
        if isinstance(status,conference.ContribStatusWithdrawn):
            res= _("""
                <tr>
                    <td align="center"><b>--_("WITHDRAWN")--</b></td>
                </tr>
                """)
        return res

    def _getWithdrawnInfoHTML(self):
        status=self._contrib.getCurrentStatus()
        if not isinstance(status,conference.ContribStatusWithdrawn):
            return ""
        comment=""
        if status.getComment()!="":
            comment="""<br><i>%s"""%self.htmlText(status.getComment())
        d=self.htmlText(status.getDate().strftime("%Y-%b-%D %H:%M"))
        resp=""
        if status.getResponsible() is not None:
            resp="by %s"%self.htmlText(status.getResponsible().getFullName())
        html = _("""
     <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Withdrawal information")</span></td>
        <td bgcolor="white" class="blacktext"><b> _("WITHDRAWN")</b> _("on") %s %s%s</td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
            """)%(d,resp,comment)
        return html

    def _getAdditionalFieldsHTML(self):
        html=""
        if self._contrib.getConference().hasEnabledSection("cfa") and self._contrib.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
            for f in self._contrib.getConference().getAbstractMgr().getAbstractFieldsMgr().getFields():
                if f.isActive():
                    id = f.getId()
                    caption = f.getName()
                    html+="""
                    <tr>
                        <td class="dataCaptionTD"><span class="dataCaptionFormat">%s</span></td>
                        <td bgcolor="white" class="blacktext"><table class="tablepre"><tr><td><pre>%s</pre></td></tr></table></td>
                    </tr>"""%(caption, self.htmlText( self._contrib.getField(id) ))
        return html


    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["eventType"] = self._eventType
        vars["withdrawnNotice"]=self._getWithdrawnNoticeHTML()
        vars["locator"] = self._contrib.getLocator().getWebForm()
        vars["title"] = self._contrib.getTitle()
        if isStringHTML(self._contrib.getDescription()):
            vars["description"] = self._contrib.getDescription()
        else:
            vars["description"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._contrib.getDescription()
        vars["additionalFields"] = self._getAdditionalFieldsHTML()
        vars["rowspan"]="6"
        tmp = WAuthorTable( self._contrib.getPrimaryAuthorList(), self._contrib )
        p = {"addAuthorsURL":quoteattr(str(urlHandlers.UHContribModNewPrimAuthor.getURL(self._contrib))), \
            "authorActionURL":quoteattr(str(urlHandlers.UHContribModPrimaryAuthorAction.getURL(self._contrib))), \
            "modAuthorURLGen":urlHandlers.UHContribModPrimAuthor.getURL,\
            "upAuthorURLGen":urlHandlers.UHContribModPrimAuthUp.getURL, \
            "downAuthorURLGen":urlHandlers.UHContribModPrimAuthDown.getURL, \
            "searchAuthorURL":quoteattr(str(urlHandlers.UHContribModPrimAuthSearch.getURL(self._contrib))), \
            "moveValue": _("to co-author")}
        vars["primAuthTable"] = tmp.getHTML(p)
        tmp = WAuthorTable( self._contrib.getCoAuthorList(), self._contrib)
        p = {"addAuthorsURL":quoteattr(str(urlHandlers.UHContribModNewCoAuthor.getURL(self._contrib))), \
            "authorActionURL":quoteattr(str(urlHandlers.UHContribModCoAuthorAction.getURL(self._contrib))), \
            "modAuthorURLGen":urlHandlers.UHContribModCoAuthor.getURL,\
            "upAuthorURLGen":urlHandlers.UHContribModCoAuthUp.getURL, \
            "downAuthorURLGen":urlHandlers.UHContribModCoAuthDown.getURL, \
            "searchAuthorURL":quoteattr(str(urlHandlers.UHContribModCoAuthSearch.getURL(self._contrib))), \
            "moveValue": _("to primary")}
        vars["coAuthTable"] = tmp.getHTML(p)
        vars["place"] = ""
        if self._contrib.getLocation():
            vars["place"]=self.htmlText(self._contrib.getLocation().getName())
        room=self._contrib.getRoom()
        if room is not None and room.getName().strip()!="":
            vars["place"]= _("""%s <br> _("Room"): %s""")%(vars["place"],self.htmlText(room.getName()))
        if self._contrib.getBoardNumber()!="" and self._contrib.getBoardNumber() is not None:
            vars["place"]= _("""%s<br> _("Board #")%s""")%(vars["place"],self.htmlText(self._contrib.getBoardNumber()))
        vars["id"] = self.htmlText( self._contrib.getId() )
        vars["dataModificationURL"] = str( urlHandlers.UHContributionDataModification.getURL( self._contrib ) )
        vars["duration"]=""
        if self._contrib.getDuration() is not None:
            vars["duration"]=(datetime(1900,1,1)+self._contrib.getDuration()).strftime("%Hh%M'")
        vars["type"] = ""
        if self._contrib.getType():
            vars["type"] = self.htmlText( self._contrib.getType().getName() )
        vars["track"] = _("""--_("none")--""")
        if self._contrib.getTrack():
            vars["track"] = """<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHTrackModification.getURL(self._contrib.getTrack()))),self.htmlText(self._contrib.getTrack().getTitle()))
        vars["session"] = ""
        if self._contrib.getSession():
            vars["session"]="""<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHSessionModification.getURL(self._contrib.getSession()))),self.htmlText(self._contrib.getSession().getTitle()))
        vars["abstract"] = ""
        if isinstance(self._contrib, conference.AcceptedContribution):
            vars["abstract"] = self._getAbstractHTML()
        vars["speakers"]=self._getSpeakersHTML()
        vars["contrib"] = self._contrib
        vars["authorsForSpeakers"]=self._getAuthorsForSpeakers()
        vars["addSpeakersURL"]=quoteattr(str(urlHandlers.UHContribModAddSpeakers.getURL(self._contrib)))
        vars["newSpeakerURL"]=quoteattr(str(urlHandlers.UHContribModNewSpeaker.getURL(self._contrib)))
        vars["remSpeakersURL"]=quoteattr(str(urlHandlers.UHContribModRemSpeakers.getURL(self._contrib)))
        vars["searchSpeakersURL"]=quoteattr(str(urlHandlers.UHContribModSpeakerSearch.getURL(self._contrib)))
        vars["selTracks"]=self._getChangeTracksHTML()
        vars["setTrackURL"]=quoteattr(str(urlHandlers.UHContribModSetTrack.getURL(self._contrib)))
        vars["selSessions"]=self._getChangeSessionsHTML()
        vars["setSessionURL"]=quoteattr(str(urlHandlers.UHContribModSetSession.getURL(self._contrib)))
        vars["contribXML"]=urlHandlers.UHContribToXMLConfManager.getURL(self._contrib)
        vars["contribPDF"]=urlHandlers.UHContribToPDFConfManager.getURL(self._contrib)
        vars["printIconURL"] = Config.getInstance().getSystemIconURL("pdf")
        vars["xmlIconURL"]=Config.getInstance().getSystemIconURL("xml")
        vars["withdrawURL"]=quoteattr(str(urlHandlers.UHContribModWithdraw.getURL(self._contrib)))
        vars["withdrawnInfo"]=self._getWithdrawnInfoHTML()
        vars["withdrawDisabled"]=False
        if isinstance(self._contrib.getCurrentStatus(),conference.ContribStatusWithdrawn):
            vars["withdrawDisabled"]=True
        vars["reportNumbersTable"]=wcomponents.WReportNumbersTable(self._contrib,"contribution").getHTML()
        vars["keywords"]=self._contrib.getKeywords()
        return vars


class WPContributionModification( WPContribModifMain ):

    def _getTabContent( self, params ):
        wc = WContribModifMain( self._contrib, materialFactories.ContribMFRegistry() )
        return wc.getHTML()

class WPContributionModificationClosed( WPContribModifMain ):

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), "")

    def _getTabContent( self, params ):
        wc = WContribModifClosed()
        return wc.getHTML()


class WContribModNewPrimAuthor(wcomponents.WTemplated):

    def __init__(self,contrib):
        self._contrib = contrib

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHContribModNewPrimAuthor.getURL(self._contrib)))
        vars["titles"]=TitlesRegistry().getSelectItemsHTML()
        return vars



class WPModNewPrimAuthor( WPContribModifMain ):

    def _getTabContent( self, params ):
        wc = WContribModNewPrimAuthor(self._contrib)
        return wc.getHTML()


class WContribModPrimAuthor(wcomponents.WTemplated):

    def __init__(self,auth):
        self._auth=auth

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHContribModPrimAuthor.getURL(self._auth)))
        vars["titles"]=TitlesRegistry.getSelectItemsHTML(self._auth.getTitle())
        vars["surName"]=quoteattr(self._auth.getFamilyName())
        vars["name"]=quoteattr(self._auth.getFirstName())
        vars["affiliation"]=quoteattr(self._auth.getAffiliation())
        vars["email"]=quoteattr(self._auth.getEmail())
        vars["address"]=self._auth.getAddress()
        vars["phone"]=quoteattr(self._auth.getPhone())
        vars["fax"]=quoteattr(self._auth.getFax())
        return vars


class WPModPrimAuthor( WPContribModifMain ):

    def _getTabContent( self, params ):
        wc = WContribModPrimAuthor(params["author"])
        return wc.getHTML()

class WContribModNewCoAuthor(wcomponents.WTemplated):

    def __init__(self,contrib):
        self._contrib = contrib

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHContribModNewCoAuthor.getURL(self._contrib)))
        vars["titles"]=TitlesRegistry().getSelectItemsHTML()
        return vars


class WPModNewCoAuthor( WPContribModifMain ):

    def _getTabContent( self, params ):
        wc = WContribModNewCoAuthor(self._contrib)
        return wc.getHTML()

class WContribModNewSpeaker(wcomponents.WTemplated):

    def __init__(self,contrib):
        self._contrib = contrib

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHContribModNewSpeaker.getURL(self._contrib)))
        vars["titles"]=TitlesRegistry().getSelectItemsHTML()
        return vars


class WPModNewSpeaker( WPContribModifMain ):

    def _getTabContent( self, params ):
        wc = WContribModNewSpeaker(self._contrib)
        return wc.getHTML()


class WContribModCoAuthor(wcomponents.WTemplated):

    def __init__(self,auth):
        self._auth=auth

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHContribModCoAuthor.getURL(self._auth)))
        vars["titles"]=TitlesRegistry.getSelectItemsHTML(self._auth.getTitle())
        vars["surName"]=quoteattr(self._auth.getFamilyName())
        vars["name"]=quoteattr(self._auth.getFirstName())
        vars["affiliation"]=quoteattr(self._auth.getAffiliation())
        vars["email"]=quoteattr(self._auth.getEmail())
        vars["address"]=self._auth.getAddress()
        vars["phone"]=quoteattr(self._auth.getPhone())
        vars["fax"]=quoteattr(self._auth.getFax())
        return vars


class WPModCoAuthor( WPContribModifMain ):

    def _getTabContent( self, params ):
        wc = WContribModCoAuthor(params["author"])
        return wc.getHTML()

class WContribModSpeaker(wcomponents.WTemplated):

    def __init__(self,auth):
        self._auth=auth

    def _getAddAsSubmitterHTML(self):
        html= _("""
                    <tr>
                        <td nowrap class="titleCellTD">
                            <span class="titleCellFormat"> _("Submission control")</span>
                        </td>
                        <td bgcolor="white" width="100%%" valign="top" class="blacktext" style="padding-left:5px">
                            %s
                        </td>
                    </tr>
                    <tr>
                        <td colspan="2">&nbsp;</td>
                    </tr>
                    """)
        from MaKaC.user import AvatarHolder
        ah = AvatarHolder()
        results=ah.match({"email":self._auth.getEmail()}, exact=1)
        if results is not None and results!=[]:
            av=results[0]
            if self._auth.getContribution().canUserSubmit(av):
                html=html%( _("""This speaker Already have submission rights."""))
            else:
                html=html% _("""<input type="checkbox" name="submissionControl"> _("Give submission rights to the speaker").""")
        elif self._auth.getEmail() in self._auth.getContribution().getSubmitterEmailList():
            html=html%( _("""This speaker Already have submission rights."""))
        else:
            html=html% _("""<input type="checkbox" name="submissionControl"> _("Give submission rights to the speaker.")<br><br><i><font color="black"><b> _("Note"): </b></font> _("This person does NOT already have an Indico account, he or she will be sent an email asking to create an account. After the account creation, the user will automatically be given submission rights.")</i>""")
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHContribModSpeaker.getURL(self._auth)))
        vars["titles"]=TitlesRegistry.getSelectItemsHTML(self._auth.getTitle())
        vars["surName"]=quoteattr(self._auth.getFamilyName())
        vars["name"]=quoteattr(self._auth.getFirstName())
        vars["affiliation"]=quoteattr(self._auth.getAffiliation())
        vars["email"]=quoteattr(self._auth.getEmail())
        vars["address"]=self._auth.getAddress()
        vars["phone"]=quoteattr(self._auth.getPhone())
        vars["fax"]=quoteattr(self._auth.getFax())
        vars["addAsSubmitter"]=self._getAddAsSubmitterHTML()
        return vars


class WPModSpeaker( WPContribModifMain ):

    def _getTabContent( self, params ):
        wc = WContribModSpeaker(params["author"])
        return wc.getHTML()

class WContribModWithdraw(wcomponents.WTemplated):

    def __init__(self,contrib):
        self._contrib=contrib

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHContribModWithdraw.getURL(self._contrib)))
        vars["comment"]=self.htmlText("")
        return vars

class WPModWithdraw(WPContribModifMain):

    def _getTabContent(self,params):
        wc=WContribModWithdraw(self._target)
        return wc.getHTML()

class WContribModifAC(wcomponents.WTemplated):

    def __init__( self, contrib ):
        self._contrib = contrib

    def _getSubmittersHTML(self):
        #return wcomponents.WPrincipalTable().getHTML( self._contrib.getSubmitterList(), self._contrib, "", "" )
        res=[]
        for sub in self._contrib.getSubmitterList():
            if sub != None:
                if type(sub) == user.Avatar:
                    res.append("""<input type="checkbox" name="selUsers" value=%s>%s"""%(quoteattr(str(sub.getId())),self.htmlText(sub.getFullName())))
                else:
                    res.append("""<input type="checkbox" name="selUsers" value=%s>%s"""%(quoteattr(str(sub.getId())),self.htmlText(sub.getName())))
        for email in self._contrib.getSubmitterEmailList():
            res.append( _("""<input type="checkbox" name="selUsers" value=%s>%s <small>( _("Pending"))</small>""")%(quoteattr(email),email))
        return "<br>".join(res)

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars( self )
        vars["submitters"]=self._getSubmittersHTML()
        vars["addSubmittersURL"]=quoteattr(str(urlHandlers.UHContribModSubmittersSel.getURL(self._contrib)))
        vars["remSubmittersURL"]=quoteattr(str(urlHandlers.UHContribModSubmittersRem.getURL(self._contrib)))
        mcf=wcomponents.WModificationControlFrame()
        addMgrURL=urlHandlers.UHContributionSelectManagers.getURL()
        remMgrURL=urlHandlers.UHContributionRemoveManagers.getURL()
        vars["modifyControlFrame"]=mcf.getHTML(self._contrib,addMgrURL,remMgrURL)
        acf=wcomponents.WAccessControlFrame()
        visURL=urlHandlers.UHContributionSetVisibility.getURL()
        addAlwURL=urlHandlers.UHContributionSelectAllowed.getURL()
        remAlwURL=urlHandlers.UHContributionRemoveAllowed.getURL()
        vars["accessControlFrame"]=acf.getHTML(self._contrib,visURL,addAlwURL,remAlwURL)
        if not self._contrib.isProtected():
            df=wcomponents.WDomainControlFrame( self._contrib )
            addDomURL=urlHandlers.UHContributionAddDomain.getURL()
            remDomURL=urlHandlers.UHContributionRemoveDomain.getURL()
            vars["accessControlFrame"] += "<br>%s"%df.getHTML(addDomURL,remDomURL)
        return vars


class WPContribModifAC( WPContributionModifBase ):

    def _setActiveTab( self ):
        self._tabAC.setActive()

    def _getTabContent( self, params ):
        wc=WContribModifAC(self._target)
        return wc.getHTML()


class WPContribModifSC( WPContributionModifBase ):

    def _setActiveTab( self ):
        self._tabSubCont.setActive()


    def _getTabContent( self, params ):

        wc = wcomponents.WContribModifSC( self._target )
        pars = { \
            "moveSubContribURL": urlHandlers.UHSubContribActions.getURL(self._contrib), \
            "addSubContURL": urlHandlers.UHContribAddSubCont.getURL(), \
            "subContModifURL": urlHandlers.UHSubContribModification.getURL, \
            "subContUpURL": urlHandlers.UHContribUpSubCont.getURL(), \
            "subContDownURL": urlHandlers.UHContribDownSubCont.getURL()}
        return wc.getHTML( pars )

#-----------------------------------------------------------------------------

class WSubContributionCreation(wcomponents.WTemplated):

    def __init__( self, target ):
        self.__owner = target

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = vars.get("title","")
        vars["description"] = vars.get("description","")
        vars["durationHours"] = vars.get("durationHours","0")
        vars["durationMinutes"] = vars.get("durationMinutes","15")
        vars["keywords"] = vars.get("keywords","")
        vars["locator"] = self.__owner.getLocator().getWebForm()
        vars["speakers"] = ""

        vars["presenterDefined"] = vars.get("presenterDefined","")
        return vars

    def _getPersonOptions(self):
        html = []
        names = []
        text = {}
        html.append("""<option value=""> </option>""")
        for contribution in self.__owner.getConference().getContributionList() :
            for speaker in contribution.getSpeakerList() :
                name = speaker.getFullNameNoTitle()
                if not(name in names) :
                    text[name] = """<option value="s%s-%s">%s</option>"""%(contribution.getId(),speaker.getId(),name)
                    names.append(name)
            for author in contribution.getAuthorList() :
                name = author.getFullNameNoTitle()
                if not name in names:
                    text[name] = """<option value="a%s-%s">%s</option>"""%(contribution.getId(),author.getId(),name)
                    names.append(name)
            for coauthor in contribution.getCoAuthorList() :
                name = coauthor.getFullNameNoTitle()
                if not name in names:
                    text[name] = """<option value="c%s-%s">%s</option>"""%(contribution.getId(),coauthor.getId(),name)
                    names.append(name)
        names.sort()
        for name in names:
            html.append(text[name])
        return "".join(html)

class WPContribAddSC( WPContributionModifBase ):

    def _setActiveTab( self ):
        self._tabSubCont.setActive()

    def _getTabContent( self, params ):

        wc = WSubContributionCreation( self._target )
        pars = { \
            "postURL": urlHandlers.UHContribCreateSubCont.getURL()}
        params.update(pars)

        wpresenter = wcomponents.WAddPersonModule("presenter")
        params["presenterOptions"] = params.get("presenterOptions",self._getPersonOptions())
        params["presenter"] = wpresenter.getHTML(params)

        return wc.getHTML( params )

    def _getPersonOptions(self):
        html = []
        names = []
        text = {}
        html.append("""<option value=""> </option>""")
        for contribution in self._contrib.getConference().getContributionList() :
            for speaker in contribution.getSpeakerList() :
                name = speaker.getFullNameNoTitle()
                if not(name in names) :
                    text[name] = """<option value="s%s-%s">%s</option>"""%(contribution.getId(),speaker.getId(),name)
                    names.append(name)
            for author in contribution.getAuthorList() :
                name = author.getFullNameNoTitle()
                if not name in names:
                    text[name] = """<option value="a%s-%s">%s</option>"""%(contribution.getId(),author.getId(),name)
                    names.append(name)
            for coauthor in contribution.getCoAuthorList() :
                name = coauthor.getFullNameNoTitle()
                if not name in names:
                    text[name] = """<option value="c%s-%s">%s</option>"""%(contribution.getId(),coauthor.getId(),name)
                    names.append(name)
        names.sort()
        for name in names:
            html.append(text[name])
        return "".join(html)

#---------------------------------------------------------------------------

class WSubContributionCreationPresenterSelect(WPContributionModifBase ):

    def _setActiveTab( self ):
        self._tabSubCont.setActive()

    def _getTabContent( self, params ):
        searchAction = str(self._rh.getCurrentURL())
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        p = wcomponents.WComplexSelection(self._conf,searchAction,forceWithoutExtAuth=searchLocal)
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WSubContributionCreationPresenterNew(WPContributionModifBase):

    def _setActiveTab( self ):
        self._tabSubCont.setActive()

    def _getTabContent( self, params ):
        p = wcomponents.WNewPerson()

        if params.get("formTitle",None) is None :
            params["formTitle"] = _("Define new presenter")
        if params.get("titleValue",None) is None :
            params["titleValue"] = ""
        if params.get("surNameValue",None) is None :
            params["surNameValue"] = ""
        if params.get("nameValue",None) is None :
            params["nameValue"] = ""
        if params.get("emailValue",None) is None :
            params["emailValue"] = ""
        if params.get("addressValue",None) is None :
            params["addressValue"] = ""
        if params.get("affiliationValue",None) is None :
            params["affiliationValue"] = ""
        if params.get("phoneValue",None) is None :
            params["phoneValue"] = ""
        if params.get("faxValue",None) is None :
            params["faxValue"] = ""

        formAction = urlHandlers.UHContribCreateSubContPersonAdd.getURL(self._contrib)
        formAction.addParam("orgin","new")
        formAction.addParam("typeName","presenter")
        params["formAction"] = formAction

        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPContributionSelectManagers( WPContribModifAC ):

    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHContributionSelectManagers.getURL(), forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHContributionAddManagers.getURL()
        return wc.getHTML( params )


class WPContributionSelectAllowed( WPContribModifAC ):

    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHContributionSelectAllowed.getURL(), forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHContributionAddAllowed.getURL()
        return wc.getHTML( params )


class WContributionDataModificationBoard(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars(self)
        return vars

class WContributionDataModificationType(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars(self)
        return vars

class WContributionDataModification(wcomponents.WTemplated):

    def __init__( self, contribution, conf, rh = None ):
        self._contrib = contribution
        self._owner = self._contrib.getOwner()
        self._conf = conf
        self._rh = rh

    def _getTypeItemsHTML(self):
        res = ["""<option value=""></option>"""]
        conf=self._contrib.getConference()
        for type in conf.getContribTypeList():
            selected=""
            if self._contrib.getType()==type:
                selected=" selected"
            res.append("""<option value=%s%s>%s</option>"""%(\
                quoteattr(str(type.getId())),selected,\
                self.htmlText(type.getName())))
        return "".join(res)

    def _getAdditionalFieldsHTML(self):
        html=""
        if self._contrib.getConference().hasEnabledSection("cfa") and \
                self._contrib.getConference().getType() == "conference" and \
                self._contrib.getConference().getAbstractMgr().hasAnyEnabledAbstractField():
            for f in self._contrib.getConference().getAbstractMgr().getAbstractFieldsMgr().getFields():
                if f.isActive():
                    id = f.getId()
                    caption = f.getName()
                    html+="""
                    <tr>
                        <td nowrap class="titleCellTD">
                            <span class="titleCellFormat">%s</span>
                        </td>
                        <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                            <textarea name="%s" cols="65" rows="10">%s</textarea>
                        </td>
                    </tr>"""%(caption, "f_%s"%id, self.htmlText(self._contrib.getField(id)))
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        defaultDefinePlace = defaultDefineRoom = ""
        defaultInheritPlace = defaultInheritRoom = "checked"
        locationName, locationAddress, roomName, defaultExistRoom = "", "", "",""
        vars["conference"] = self._conf
        vars["boardNumber"]=quoteattr(str(self._contrib.getBoardNumber()))
        vars["contrib"] = self._contrib
        vars["title"] = quoteattr(self._contrib.getTitle())
        vars["description"] = self.htmlText(self._contrib.getDescription())
        vars["additionalFields"] = self._getAdditionalFieldsHTML()
        vars["day"],vars["month"],vars["year"]="","",""
        vars["sHour"],vars["sMinute"]="",""
        sDate=self._contrib.getStartDate()
        if sDate is not None:
            vars["day"]=quoteattr(str(sDate.day))
            vars["month"] = quoteattr(str(sDate.month))
            vars["year"] = quoteattr(str(sDate.year))
            vars["sHour"] = quoteattr(str(sDate.hour))
            vars["sMinute"] = quoteattr(str(sDate.minute))
        if self._contrib.getStartDate():
            vars["dateTime"] = formatDateTime(self._contrib.getAdjustedStartDate())
        else:
            vars["dateTime"] = ""
        vars["duration"] = self._contrib.getDuration().seconds/60
        if self._contrib.getDuration() is not None:
            vars["durationHours"]=quoteattr(str((datetime(1900,1,1)+self._contrib.getDuration()).hour))
            vars["durationMinutes"]=quoteattr(str((datetime(1900,1,1)+self._contrib.getDuration()).minute))
        if self._contrib.getOwnLocation():
            defaultDefinePlace = "checked"
            defaultInheritPlace = ""
            locationName = self._contrib.getLocation().getName()
            locationAddress = self._contrib.getLocation().getAddress()

        if self._contrib.getOwnRoom():
            defaultDefineRoom= "checked"
            defaultInheritRoom = ""
            defaultExistRoom=""
            roomName = self._contrib.getRoom().getName()
        vars["defaultInheritPlace"] = defaultInheritPlace
        vars["defaultDefinePlace"] = defaultDefinePlace
        vars["confPlace"] = ""
        confLocation = self._owner.getLocation()
        if self._contrib.isScheduled():
            confLocation=self._contrib.getSchEntry().getSchedule().getOwner().getLocation()
        if self._contrib.getSession() and not self._contrib.getConference().getEnableSessionSlots():
            confLocation = self._contrib.getSession().getLocation()
        if confLocation:
            vars["confPlace"] = confLocation.getName()
        vars["locationName"] = locationName
        vars["locationAddress"] = locationAddress
        vars["defaultInheritRoom"] = defaultInheritRoom
        vars["defaultDefineRoom"] = defaultDefineRoom
        vars["defaultExistRoom"] = defaultExistRoom
        vars["confRoom"] = ""
        confRoom = self._owner.getRoom()
        rx=[]
        roomsexist = self._conf.getRoomList()
        roomsexist.sort()
        for room in roomsexist:
            sel=""
            rx.append("""<option value=%s%s>%s</option>"""%(quoteattr(str(room)),
                        sel,self.htmlText(room)))
        vars ["roomsexist"] = "".join(rx)
        if self._contrib.isScheduled():
            confRoom=self._contrib.getSchEntry().getSchedule().getOwner().getRoom()
        if self._contrib.getSession() and not self._contrib.getConference().getEnableSessionSlots():
            confRoom = self._contrib.getSession().getRoom()
        if confRoom:
            vars["confRoom"] = confRoom.getName()
        vars["roomName"] = quoteattr(roomName)
        vars["parentType"] = "conference"
        if self._contrib.getSession() is not None:
            vars["parentType"] = "session"
            if self._contrib.isScheduled() and self._contrib.getConference().getEnableSessionSlots():
                vars["parentType"]="session slot"
        vars["postURL"] = urlHandlers.UHContributionDataModif.getURL(self._contrib)
        vars["types"]=self._getTypeItemsHTML()
        vars["keywords"]=self._contrib.getKeywords()
        import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
        wr = webFactoryRegistry.WebFactoryRegistry()
        wf = wr.getFactory(self._conf)
        if wf != None:
            type = wf.getId()
        else:
            type = "conference"
        if type == "conference":
            vars["Type"]=WContributionDataModificationType().getHTML(vars)
            vars["Board"]=WContributionDataModificationBoard().getHTML(vars)
        else:
            vars["Type"]=""
            vars["Board"]=""

        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["useRoomBookingModule"] = minfo.getRoomBookingModuleActive()
        return vars


class WPEditData(WPContribModifMain):

    def _getTabContent( self, params ):
        wc = WContributionDataModification(self._target, self._conf)

        pars = {"postURL": urlHandlers.UHConfPerformAddContribution.getURL(), \
        "calendarIconURL": Config.getInstance().getSystemIconURL( "calendar" ), \
        "calendarSelectURL":  urlHandlers.UHSimpleCalendar.getURL() }
        return wc.getHTML( pars )


class WPContribAddMaterial( WPContribModifMain ):

    def __init__( self, rh, contrib, mf ):
        WPContribModifMain.__init__( self, rh, contrib )
        self._mf = mf

    def _getTabContent( self, params ):
        if self._mf:
            comp = self._mf.getCreationWC( self._target )
        else:
            comp = wcomponents.WMaterialCreation( self._target )
        pars = { "postURL": urlHandlers.UHContributionPerformAddMaterial.getURL() }
        return comp.getHTML( pars )

class WPContributionDeletion( WPContributionModifTools ):

    def _getTabContent( self, params ):
        wc = wcomponents.WContributionDeletion( [self._target] )
        return wc.getHTML( urlHandlers.UHContributionDelete.getURL( self._target ) )


class WContributionMove(wcomponents.WTemplated):

    def __init__(self, contrib, conf ):
        self._contrib = contrib
        self._conf = conf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        sesList = ""
        if self._contrib.getOwner() != self._conf:
            sesList = _("""<option value=\"CONF\" > _("Conference") : %s</option>\n""")%self._conf.getTitle()
        for ses in self._conf.getSessionListSorted():
            if self._contrib.getOwner() != ses:
                sesList = sesList + _("""<option value=\"%s\" > _("Session") : %s</option>\n""")%(ses.getId(), ses.getTitle())
        vars["sessionList"] = sesList
        vars["confId"] = self._conf.getId()
        vars["contribId"] = self._contrib.getId()
        return vars


class WPcontribMove( WPContributionModifTools ):

    def _getTabContent( self, params ):
        wc = WContributionMove( self._target, self._target.getConference() )
        params["cancelURL"] = urlHandlers.UHContribModifTools.getURL( self._target )
        params["moveURL"] = urlHandlers.UHContributionPerformMove.getURL()
        return wc.getHTML( params )

class WPContributionWriteMinutes( WPContributionModifTools ):

    def _getTabContent( self, params ):
        wc = wcomponents.WWriteMinutes( self._target )
        pars = {"postURL": urlHandlers.UHContributionWriteMinutes.getURL(self._target) }
        return wc.getHTML( pars )


class WPModSubmittersSel(WPContribModifAC):

    def _getTabContent(self,params):
        wf=self._rh.getWebFactory()
        addTo=1
        if wf is not None:
            addTo=4
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc=wcomponents.WPrincipalSelection(urlHandlers.UHContribModSubmittersSel.getURL(), addTo=addTo, forceWithoutExtAuth=searchLocal)
        wc.setTitle( _("Selecting users allowed to submit material"))
        params["addURL"]=urlHandlers.UHContribModSubmittersAdd.getURL()
        return wc.getHTML( params )

class WPContributionDisplayRemoveMaterialsConfirm( WPContributionDefaultDisplayBase ):

    def __init__(self,rh, conf, mat):
        WPContributionDefaultDisplayBase.__init__(self,rh,conf)
        self._mat=mat

    def _getBody(self,params):
        wc=wcomponents.WDisplayConfirmation()
        msg= _(""" _("Are you sure you want to delete the following material")?<br>
        <b><i>%s</i></b>
        <br>""")%self._mat.getTitle()
        url=urlHandlers.UHContributionDisplayRemoveMaterial.getURL(self._mat.getOwner())
        return wc.getHTML(msg,url,{"deleteMaterial":self._mat.getId()})

class WPContribDisplayWriteMinutes( WPContributionDefaultDisplayBase ):

    def _getBody( self, params ):
        wc = wcomponents.WWriteMinutes( self._contrib )
        pars = {"postURL": urlHandlers.UHContributionDisplayWriteMinutes.getURL(self._contrib) }
        return wc.getHTML( pars )


class WPContributionReportNumberEdit(WPContributionModifBase):

    def __init__(self, rh, contribution, reportNumberSystem):
        WPContributionModifBase.__init__(self, rh, contribution)
        self._reportNumberSystem=reportNumberSystem

    def _getTabContent( self, params):
        wc=wcomponents.WModifReportNumberEdit(self._target, self._reportNumberSystem, "contribution")
        return wc.getHTML()
