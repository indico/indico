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

from xml.sax.saxutils import quoteattr
import urllib

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.navigation as navigation
import MaKaC.review as review
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase, WPConferenceModifAbstractBase
from MaKaC.common import Config
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from MaKaC.common.timezoneUtils import nowutc, getAdjustedDate, DisplayTZ
from MaKaC.common import Configuration
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.conference import ILocalFileAbstractMaterialFossil


class WConfCFADeactivated(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw


class WPCFAInactive( WPConferenceDefaultDisplayBase ):

    def _getBody( self, params ):
        wc = WConfCFADeactivated( self._getAW(), self._conf )
        return wc.getHTML()


class WCFANotYetOpened(wcomponents.WTemplated):
    pass


class WPCFANotYetOpened( WPConferenceDefaultDisplayBase ):

    def _getBody( self, params ):
        wc = WCFANotYetOpened()
        return wc.getHTML()


class WCFAClosed(wcomponents.WTemplated):
    pass


class WPCFAClosed( WPConferenceDefaultDisplayBase ):

    def _getBody( self, params ):
        wc = WCFAClosed()
        return wc.getHTML()


class WConfCFA(wcomponents.WTemplated):

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def _getActionsHTML( self, showActions = False ):
        html = ""
        if showActions:
            cfa = self._conf.getAbstractMgr()
            if nowutc() < cfa.getStartSubmissionDate():
                return html
            else:
                submitOpt = ""
                if cfa.inSubmissionPeriod():
                    submitOpt = i18nformat("""<li><a href="%s"> _("Submit a new abstract")</a></li>""")%(urlHandlers.UHAbstractSubmission.getURL( self._conf ))
                html = i18nformat("""
                <b> _("Possible actions you can carry out"):</b>
                <ul>
                    %s
                    <li><a href="%s"> _("View or modify your already submitted abstracts")</a></li>
                </ul>
                       """)%( submitOpt, urlHandlers.UHUserAbstracts.getURL( self._conf ) )
        return html


    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        cfa = self._conf.getAbstractMgr()
        if cfa.inSubmissionPeriod():
            vars["status"] = _("OPENED")
        else:
            vars["status"] = _("CLOSED")
        vars["startDate"] = cfa.getStartSubmissionDate().strftime("%d %B %Y")
        vars["endDate"] = cfa.getEndSubmissionDate().strftime("%d %B %Y")
        vars["actions"] = self._getActionsHTML(vars["menuStatus"] == "close")
        vars["announcement"] = cfa.getAnnouncement()
        return vars


class WPConferenceCFA( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NEConferenceCFA

    def _getBody( self, params ):
        wc = WConfCFA( self._getAW(), self._conf )
        pars = {"menuStatus":self._rh._getSession().getVar("menuStatus") or "open"}
        return wc.getHTML( pars )

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._cfaOpt)


class WPAbstractSubmission( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NEAbstractSubmission

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
           self._includeJSPackage('Management')

    def _getBody( self, params ):
        params["postURL"] = urlHandlers.UHAbstractSubmission.getURL( self._conf )
        params["origin"] = "display"
        wc = WAbstractDataModification( self._conf )
        return wc.getHTML( params )

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._cfaNewSubmissionOpt)



class WUserAbstracts( wcomponents.WTemplated ):

    def __init__( self, aw, conf ):
        self._aw = aw
        self._conf = conf

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        cfaMgr = self._conf.getAbstractMgr()

        tzUtil = DisplayTZ(self._aw,self._conf)
        tz = tzUtil.getDisplayTZ()

        l = cfaMgr.getAbstractListForAvatar( self._aw.getUser() )
        l += cfaMgr.getAbstractListForAuthorEmail(self._aw.getUser().getEmail())

        l = sorted(set(l), key=lambda i:int(i.getId()))

        if not l:
            vars["abstracts"] = i18nformat("""<tr>
                                        <td align="center" colspan="4" bgcolor="white">
                                            <br>
                                            --_("No submitted abstract found within this conference")--
                                        </td>
                                    </tr>
                                    """)
        else:
            res = []
            for abstract in l:
                status = abstract.getCurrentStatus()
                statusLabel = _("SUBMITTED")
                if isinstance( status, review.AbstractStatusAccepted ):
                    statusLabel = _("ACCEPTED")
                    if status.getType() is not None and status.getType()!="":
                        statusLabel="%s as %s"%(statusLabel,status.getType().getName())
                elif isinstance( status, review.AbstractStatusRejected ):
                    statusLabel = _("REJECTED")
                elif isinstance( status, review.AbstractStatusWithdrawn ):
                    statusLabel = _("WITHDRAWN")
                elif isinstance(status,review.AbstractStatusDuplicated):
                    statusLabel = _("DUPLICATED")
                elif isinstance(status,review.AbstractStatusMerged):
                    statusLabel = _("MERGED")
                res.append("""
                <tr>
                    <td class="abstractLeftDataCell">%s</td>
                    <td class="abstractDataCell"><input type="checkbox" name="abstracts" value=%s><a href=%s>%s</a></td>
                    <td class="abstractDataCell" nowrap>%s</td>
                    <td class="abstractDataCell">%s</td>
                </tr>"""%( \
        abstract.getId(), \
        quoteattr(abstract.getId()), \
        quoteattr(str(urlHandlers.UHAbstractDisplay.getURL(abstract))), \
        self.htmlText( abstract.getTitle() ), statusLabel, \
        getAdjustedDate(abstract.getModificationDate(),tz=tz).strftime("%Y-%m-%d %H:%M")))
            vars["abstracts"] = "".join(res)
        vars["abstractsPDFURL"]=quoteattr(str(urlHandlers.UHAbstractsDisplayPDF.getURL(self._conf)))
        return vars


class WPUserAbstracts( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NEUserAbstracts

    def _getBody( self, params ):
        wc = WUserAbstracts( self._getAW(), self._conf )
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._cfaViewSubmissionsOpt)


class WPAbstractDisplayBase( WPConferenceDefaultDisplayBase ):

    def __init__( self, rh, abstract ):
        conf = abstract.getConference()
        WPConferenceDefaultDisplayBase.__init__( self, rh, conf )
        self._navigationTarget = self._abstract = abstract


class WAbstractCannotBeModified( wcomponents.WTemplated ):

    def __init__( self, abstract ):
        self._abstract = abstract


class WPAbstractCannotBeModified( WPAbstractDisplayBase ):

    def _getBody( self, params ):
        wc = WAbstractCannotBeModified( self._abstract )
        return wc.getHTML()


class WAbstractSubmissionConfirmation( wcomponents.WTemplated ):

    def __init__( self, aw, abstract ):
        self._aw = aw
        self._abstract = abstract

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["displayURL"] = quoteattr( str ( urlHandlers.UHAbstractDisplay.getURL( self._abstract ) ) )
        vars["displayURLText"] = self.htmlText( str( urlHandlers.UHAbstractDisplay.getURL( self._abstract ) ) )
        conf = self._abstract.getConference()
        vars["userAbstractsURL"] = quoteattr( str ( urlHandlers.UHUserAbstracts.getURL( conf ) ) )
        vars["userAbstractsURLText"] = self.htmlText( str ( urlHandlers.UHUserAbstracts.getURL( conf ) ) )
        vars["CFAURL"] = quoteattr( str ( urlHandlers.UHConferenceCFA.getURL( conf ) ) )
        vars["abstractId"] = self._abstract.getId()
        return vars


class WPAbstractSubmissionConfirmation( WPAbstractDisplayBase ):
    navigationEntry = navigation.NEAbstractSubmissionConfirmation

    def _getBody( self, params ):
        wc = WAbstractSubmissionConfirmation( self._getAW(), self._abstract )
        return wc.getHTML()


class WAbstractDisplay( wcomponents.WTemplated ):

    def __init__(self, aw, abstract):
        self._abstract = abstract
        self._aw = aw

    def _getAuthorHTML( self, author ):
        res = "%s, %s"%(author.getSurName().upper(), author.getFirstName())
        if author.getAffiliation() != "":
            res = "%s (%s)"%(res, author.getAffiliation())
        return self.htmlText( res )

    def _getAdditionalFieldsHTML(self):
        html=""
        afm = self._abstract.getConference().getAbstractMgr().getAbstractFieldsMgr()
        for f in afm.getActiveFields():
            id = f.getId()
            caption = f.getName()
            html+="""
                                        <tr>
                                            <td>
                                                <table width="100%%" cellspacing="0">
                                                    <tr>
                                                        <td class="displayField" valign="top" width="1%%" nowrap><b>%s:</b></td>
                                                    </tr>
                                                    <tr>
                                                        <td valign="top"><table class="tablepre"><tr><td><pre>%s</pre></td></tr></table></td>
                                                    </tr>
                                                </table>
                                            </td>
                                        </tr>
                """%(caption, self.htmlText(self._abstract.getField(id)) )
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        tzUtil = DisplayTZ(self._aw, self._abstract.getConference())
        tz = tzUtil.getDisplayTZ()

        vars["title"] = self.htmlText( self._abstract.getTitle() )
        vars["additionalFields"] = self._getAdditionalFieldsHTML()
        vars["primary_authors"] = i18nformat("""--_("none")--""")
        vars["authors"] = i18nformat("""--_("none")--""")
        primary = []
        for author in self._abstract.getPrimaryAuthorList():
            primary.append( self._getAuthorHTML( author ) )
        authors = []
        for author in self._abstract.getCoAuthorList():
            authors.append( self._getAuthorHTML( author ) )
        if primary:
            vars["primary_authors"] = "<br>".join( primary )
        if authors:
            vars["authors"] = "<br>".join( authors )
        vars["speakers"] = i18nformat("""--_("none")--""")
        speakers = []
        for spk in self._abstract.getSpeakerList():
            speakers.append( "%s"%self.htmlText( spk.getFullName() ) )
        if speakers:
            vars["speakers"] = "<br>".join( speakers )
        vars["tracks"] = i18nformat("""--_("none")--""")
        vars["contribType"] = i18nformat("""--_("none")--""")
        status=self._abstract.getCurrentStatus()
        if isinstance(status,review.AbstractStatusAccepted):
            vars["contribType"]= i18nformat("""--_("none")--""")
            if status.getType() is not None:
                vars["contribType"]=self.htmlText(status.getType().getName())
            vars["tracks"]=""
            if status.getTrack() is not None:
                vars["tracks"]=self.htmlText(status.getTrack().getTitle())
        else:
            tracks = []
            for track in self._abstract.getTrackListSorted():
                tracks.append( self.htmlText( track.getTitle() ) )
            if tracks:
                vars["tracks"] = ", ".join( tracks )
            if self._abstract.getContribType() is not None and \
                    self._abstract.getContribType()!="":
                vars["contribType"]=self.htmlText(self._abstract.getContribType().getName())
        if self._abstract.getConference().getContribTypeList() != []:
            vars["contribType"]= i18nformat("""
                                <tr>
                                    <td>
                                        <table width="100%%" cellspacing="0">
                                            <tr>
                                                <td nowrap class="displayField" valign="top"><b> _("Contribution type"):</b></td>
                                                <td width="100%%">%s</td>
                                            </tr>
                                        </table>
                                    </td>
                                        </tr>
                                """%vars["contribType"])
        else:
            vars["contribType"]=""
        vars["submitter"] = "%s"%self.htmlText( self._abstract.getSubmitter().getFullName() )
        vars["submissionDate"] = getAdjustedDate(self._abstract.getSubmissionDate(),tz=tz).strftime("%d %B %Y %H:%M")
        vars["modificationDate"] = getAdjustedDate(self._abstract.getModificationDate(),tz=tz).strftime("%d %B %Y %H:%M")
        vars["modifyURL"] = quoteattr( str( urlHandlers.UHAbstractModify.getURL( self._abstract ) ) )
        vars["withdrawURL"] = quoteattr( str( urlHandlers.UHAbstractWithdraw.getURL( self._abstract ) ) )
        vars["status"] = _("SUBMITTED")
        vars["btnWithdrawDisabled"] = ""
        vars["btnModifyDisabled"] = ""
        vars["btnRecover"] = ""
        vars["btnManageMaterialDisabled"] = "disabled"
        if not isinstance( status, review.AbstractStatusSubmitted ):
            vars["btnModifyDisabled"] = "disabled"
        if isinstance( status, review.AbstractStatusAccepted ):
            vars["status"] = _("ACCEPTED")
            vars["btnWithdrawDisabled"] = "disabled"
            vars["btnModifyDisabled"] = "disabled"
            vars["btnManageMaterialDisabled"] = ""
        elif isinstance( status, review.AbstractStatusRejected ):
            vars["status"] = _("REJECTED")
            vars["btnModifyDisabled"] = "disabled"
            vars["btnWithdrawDisabled"] = "disabled"
        elif isinstance( status, review.AbstractStatusWithdrawn ):
            vars["status"] = i18nformat(""" _("WITHDRAWN") <font size="-1">by %s _("on") %s</font>""")%(self.htmlText(status.getResponsible().getFullName()),getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M"))
            if status.getComments().strip() != "":
                vars["status"] = """%s<br><i>%s</i>"""%(vars["status"],self.htmlText(status.getComments()))
            vars["btnWithdrawDisabled"] = "disabled"
            vars["btnRecover"] = i18nformat("""<form action=%s method="POST">
                                        <td>
                                            <input type="submit" class="btn" value="_("recover")">
                                        </td>
                                    </form>
                                """)%( quoteattr( str( urlHandlers.UHAbstractRecovery.getURL( self._abstract ) ) ))
        elif isinstance(status,review.AbstractStatusDuplicated):
            vars["status"] = _("DUPLICATED")
            vars["btnModifyDisabled"]="disabled"
            vars["btnWithdrawDisabled"]="disabled"
            vars["btnManageMaterialDisabled"] = "disabled"
        elif isinstance(status,review.AbstractStatusMerged):
            target=status.getTargetAbstract()
            vars["status"] = i18nformat(""" _("MERGED") into %s-%s""")%(self.htmlText(target.getId()),self.htmlText(target.getTitle()))
            vars["btnModifyDisabled"]="disabled"
            vars["btnWithdrawDisabled"]="disabled"
            vars["btnManageMaterialDisabled"] = "disabled"
        elif isinstance(status, review.AbstractStatusProposedToAccept) or isinstance(status, review.AbstractStatusProposedToReject):
            vars["status"] = "UNDER REVIEW"
        vars["comments"] = self.htmlText( self._abstract.getComments() )
        vars["abstractId"] = self._abstract.getId()
        vars["attachments"] = fossilize(self._abstract.getAttachments().values(), ILocalFileAbstractMaterialFossil)
        return vars


class WPAbstractDisplay( WPAbstractDisplayBase ):
    navigationEntry = navigation.NEAbstractDisplay

    def _getBody( self, params ):
        wc = WAbstractDisplay( self._getAW(), self._abstract )
        return wc.getHTML()

    def _defineToolBar(self):
        pdf=wcomponents.WTBItem( _("get PDF of the programme"),
            icon = Config.getInstance().getSystemIconURL("pdf"),
            actionURL=urlHandlers.UHAbstractDisplayPDF.getURL(self._abstract))
        self._toolBar.addItem(pdf)


class WAbstractDataModification( wcomponents.WTemplated ):

    def __init__( self, conf ):
        self._conf = conf
        self._limitedFieldList = []
        self._mandatoryFieldList = [] # all mandatory fields ids, except which are also limited

    def _setMandatoryAndLimitedFields(self):
        abfm = self._conf.getAbstractMgr().getAbstractFieldsMgr()
        for f in abfm.getFields():
            id = f.getId()
            if f.isActive():
                maxLength = int(f.getMaxLength())
                isMandatory = f.isMandatory()
                if maxLength > 0: # it means there is a limit for the field in words or in characters
                    self._limitedFieldList.append(["f_"+id, maxLength, "maxLimitionCounter_"+id.replace(" ", "_"), f.getLimitation(), str(isMandatory)]) # append the textarea/input id
                else:
                    if isMandatory:
                        self._mandatoryFieldList.append("f_"+id)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["postURL"] = quoteattr(str( vars["postURL"]))
        vars["origin"] = vars.get("origin", "display")
        vars["title"] = quoteattr(str(vars.get("title", "")))
        vars["prAuthors"] = fossilize(vars.get("prAuthors", []))
        vars["coAuthors"] = fossilize(vars.get("coAuthors", []))
        cfaMgr = self._conf.getAbstractMgr()
        vars["tracksMandatory"] = cfaMgr.areTracksMandatory()
        vars["tracks"] = self._conf.getTrackList()
        if cfaMgr.getMultipleTracks():
            vars["trackListType"] = "checkbox"
        else:
            vars["trackListType"] = "radio"
        vars["tracksSelected"] = vars.get("tracksSelectedList", []) # list of track ids that had been selected
        vars["types"] = self._conf.getContribTypeList()
        vars["typeSelected"] = vars.get("type", None)
        vars["comments"] = str(vars.get("comments", ""))
        fieldDict = {}
        for field in cfaMgr.getAbstractFieldsMgr().getFields():
            f_id = "f_" + field.getId()
            fieldDict[f_id] = vars.get(f_id, "")
        vars["fieldsDict"] = fieldDict
        vars["additionalFields"] = cfaMgr.getAbstractFieldsMgr().getFields()
        self._setMandatoryAndLimitedFields()
        vars["limitedFieldList"] = self._limitedFieldList
        vars["mandatoryFieldList"] = self._mandatoryFieldList
        vars["attachedFilesAllowed"] = cfaMgr.canAttachFiles()
        vars["errorList"] = vars.get("errors", [])
        #TODO: In case of error we will lose the attached files, we should keep them somehow
        vars["attachments"] = fossilize(vars.get("attachments", []), ILocalFileAbstractMaterialFossil)
        return vars


class WPAbstractModify( WPAbstractDisplayBase ):
    navigationEntry = navigation.NEAbstractModify

    def getJSFiles(self):
        return WPAbstractDisplayBase.getJSFiles(self) + \
               self._includeJSPackage('Management')

    def _getBody( self, params ):
        params["postURL"] = urlHandlers.UHAbstractModify.getURL( self._abstract )
        wc = WAbstractDataModification( self._abstract.getConference() )
        return wc.getHTML( params )


class WAbstractWithdraw( wcomponents.WTemplated ):

    def __init__( self, abstract ):
        self._abstract = abstract

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self.htmlText( self._abstract.getTitle() )
        vars["postURL"] = urlHandlers.UHAbstractWithdraw.getURL( self._abstract )
        return vars


class WPAbstractWithdraw( WPAbstractDisplayBase ):
    navigationEntry = navigation.NEAbstractWithdraw

    def _getBody( self, params ):
        wc = WAbstractWithdraw( self._abstract )
        return wc.getHTML()


class WAbstractRecovery( wcomponents.WTemplated ):

    def __init__( self, abstract ):
        self._abstract = abstract

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self.htmlText( self._abstract.getTitle() )
        vars["postURL"] = urlHandlers.UHAbstractRecovery.getURL( self._abstract )
        return vars


class WPAbstractRecovery( WPAbstractDisplayBase ):
    navigationEntry = navigation.NEAbstractRecovery

    def _getBody( self, params ):
        wc = WAbstractRecovery( self._abstract )
        return wc.getHTML()


class WPAbstractManagementBase( WPConferenceModifBase ):

    def __init__( self, rh, abstract ):
        self._abstract = self._target = abstract
        WPConferenceModifBase.__init__( self, rh, self._abstract.getConference() )

    def _getNavigationDrawer(self):
        pars = {"target": self._abstract, "isModif": True}
        return wcomponents.WNavigationDrawer( pars )

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab("main", _("Main"), \
            urlHandlers.UHAbstractManagment.getURL( self._abstract ) )
        self._tabTracks = self._tabCtrl.newTab("tracks", _("Track judgments"), \
            urlHandlers.UHAbstractTrackProposalManagment.getURL(self._abstract))
        #self._tabAC=self._tabCtrl.newTab("ac", "Access control", \
        #        urlHandlers.UHAbstractModAC.getURL( self._abstract))
        nComments=""
        if len(self._abstract.getIntCommentList()) > 0:
            nComments = " (%s)"%len(self._abstract.getIntCommentList())
        self._tabComments=self._tabCtrl.newTab("comments", _("Internal comments%s")%nComments,\
            urlHandlers.UHAbstractModIntComments.getURL( self._abstract))
        self._tabNotifLog=self._tabCtrl.newTab("notif_log", _("Notification log"),\
            urlHandlers.UHAbstractModNotifLog.getURL( self._abstract))
        self._tabTools=self._tabCtrl.newTab("tools", _("Tools"),\
            urlHandlers.UHAbstractModTools.getURL( self._abstract))

        # Sub tabs for the track judgements
        self._subTabTrack = self._tabTracks.newSubTab( "byTrack", "Judgement details",\
                urlHandlers.UHAbstractTrackProposalManagment.getURL(self._abstract))
        self._subTabRating = self._tabTracks.newSubTab( "byRating", "Rating per question",\
                urlHandlers.UHAbstractTrackOrderByRating.getURL(self._abstract))

        self._setActiveTab()

    def _getPageContent( self, params ):
        self._createTabCtrl()

        banner = wcomponents.WAbstractBannerModif(self._abstract).getHTML()
        html = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner + html

    def _setActiveSideMenuItem(self):
        self._abstractMenuItem.setActive(True)

    def _getTabContent( self, params ):
        return "nothing"


class WAbstractManagment( wcomponents.WTemplated ):

    def __init__( self, aw, abstract ):
        self._abstract = abstract
        self._aw = aw
        self._conf = abstract.getOwner().getOwner()

    def _getAuthorHTML( self, auth ):
        tmp = "%s (%s)"%(auth.getFullName(), auth.getAffiliation())
        tmp = self.htmlText( tmp )
        if auth.getEmail() != "":
            mailtoSubject = i18nformat("""[%s] _("Abstract") %s: %s""")%( self._conf.getTitle(), self._abstract.getId(), self._abstract.getTitle() )
            mailtoURL = "mailto:%s?subject=%s"%( auth.getEmail(), urllib.quote( mailtoSubject ) )
            href = quoteattr( mailtoURL )
            tmp = """<a href=%s>%s</a>"""%(href, tmp)
        return tmp

    def _getStatusHTML( self ):
        status = self._abstract.getCurrentStatus()
        html = """<b>%s</b>"""%AbstractStatusList.getInstance().getCaption( status.__class__ ).upper()
        tzUtil = DisplayTZ(self._aw,self._conf)
        tz = tzUtil.getDisplayTZ()
        respPerson = i18nformat(""" _("by") %s""")%self._getAuthorHTML(status.getResponsible()) if status.getResponsible() else ""

        if status.__class__  == review.AbstractStatusAccepted:
            trackTitle, contribTitle = "", ""
            if status.getTrack():
                trackTitle = " for %s"%self.htmlText(status.getTrack().getTitle())
            if status.getType():
                contribTitle = " as %s"%self.htmlText(status.getType().getName())
            html = i18nformat("""%s%s%s<br><font size="-1">%s _("on") %s</font>""")%( \
                            html, trackTitle, contribTitle,\
                            respPerson, \
                            getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M") )
            if status.getComments() != "":
                html = """%s<br><font size="-1"><i>%s</i></font>"""%(\
                                                    html, status.getComments() )
        elif status.__class__ == review.AbstractStatusRejected:
            html = i18nformat("""%s<br><font size="-1">%s _("on") %s</font>""")%( \
                            html, \
                            respPerson, \
                            getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M") )
            if status.getComments() != "":
                html = """%s<br><font size="-1"><i>%s</i></font>"""%(\
                                                    html, status.getComments() )
        elif status.__class__ == review.AbstractStatusWithdrawn:
            html = i18nformat("""%s<font size="-1">%s _("on") %s</font>""")%( \
                            html,\
                            respPerson, \
                            getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M") )
            if status.getComments() != "":
                html = """%s<br><font size="-1"><i>%s</i></font>"""%(\
                                                    html, status.getComments() )
        elif status.__class__ == review.AbstractStatusDuplicated:
            original=status.getOriginal()
            url=urlHandlers.UHAbstractManagment.getURL(original)
            html = i18nformat("""%s (<a href=%s>%s-<i>%s</i></a>) <font size="-1">%s _("on") %s</font>""")%( html, quoteattr(str(url)), self.htmlText(original.getId()),\
                self.htmlText(original.getTitle()),\
                respPerson, \
                getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M") )
            if status.getComments() != "":
                html = """%s<br><font size="-1"><i>%s</i></font>"""%(\
                                                    html, status.getComments() )
        elif status.__class__ == review.AbstractStatusMerged:
            target=status.getTargetAbstract()
            url=urlHandlers.UHAbstractManagment.getURL(target)
            html = i18nformat("""<font color="black"><b>%s</b></font> (<a href=%s>%s-<i>%s</i></a>) <font size="-1">%s _("on") %s</font>""")%( html, quoteattr(str(url)), self.htmlText(target.getId()),\
                self.htmlText(target.getTitle()),\
                respPerson, \
                getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M") )
            if status.getComments() != "":
                html = """%s<br><font size="-1"><i>%s</i></font>"""%(\
                                                    html, status.getComments() )
        return html

    def _getTracksHTML( self ):
        prog = []
        for track in self._abstract.getTrackListSorted():
            jud = self._abstract.getTrackJudgement(track)
            if jud.__class__ == review.AbstractAcceptance:
                cTypeCaption=""
                if jud.getContribType() is not None:
                    cTypeCaption=jud.getContribType().getName()
                st = i18nformat(""" - _("Proposed to accept") (%s)""")%(self.htmlText(cTypeCaption))
                color = """ color="#009933" """
            elif jud.__class__ == review.AbstractRejection:
                st = i18nformat("""- _("Proposed to reject")""")
                color = """ color="red" """
            elif jud.__class__ == review.AbstractReallocation:
                st = i18nformat("""- _("Proposed for other tracks")""")
                color = """ color="black" """
            else:
                st = ""
                color = ""
            if st != "":
                prog.append( """<li>%s <font size="-1" %s> %s </font></li>"""%(self.htmlText( track.getTitle() ), color, st) )
            else:
                prog.append( """<li>%s</li>"""%(self.htmlText( track.getTitle() )) )
        return "<ul>%s</ul>"%"".join( prog )

    def _getContributionHTML( self ):
        res = ""
        contrib = self._abstract.getContribution()
        if contrib:
            url = urlHandlers.UHContributionModification.getURL(contrib)
            title = self.htmlText(contrib.getTitle())
            id = self.htmlText(contrib.getId())
            res = """<a href=%s>%s - %s</a>"""%(quoteattr(str(url)),id,title)
        return res

    def _getMergeFromHTML(self):
        abstracts = self._abstract.getMergeFromList()
        if not abstracts:
            return ""
        l = []
        for abstract in abstracts:
            if abstract.getOwner():
                l.append("""<a href="%s">%s : %s</a><br>\n"""%(urlHandlers.UHAbstractManagment.getURL(abstract), abstract.getId(), abstract.getTitle()))
            else:
                l.append("""%s : %s [DELETED]<br>\n"""%(abstract.getId(), abstract.getTitle()))

        return i18nformat("""<tr>
                    <td class="dataCaptionTD" nowrap><span class="dataCaptionFormat"> _("Merged from")</span></td>
                    <td bgcolor="white" valign="top" colspan="3">%s</td>
                </tr>""")%"".join(l)

    def _getAdditionalFieldsHTML(self):
        html=""
        afm = self._abstract.getConference().getAbstractMgr().getAbstractFieldsMgr()
        for f in afm.getActiveFields():
            id = f.getId()
            caption = f.getName()
            html+="""
                    <tr>
                        <td class="dataCaptionTD" valign="top"><span class="dataCaptionFormat">%s</span></td>
                        <td bgcolor="white" valign="top"><table class="tablepre"><tr><td><pre>%s</pre></td></tr></table></td>
                    </tr>
                """%(self.htmlText(caption), self.htmlText(self._abstract.getField(id)) )
        return html

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["title"] = self.htmlText(self._abstract.getTitle())
        vars["additionalFields"] = self._getAdditionalFieldsHTML()
        vars["organisation"] = self.htmlText(self._abstract.getSubmitter().getAffiliation())
        vars["status"] = self._getStatusHTML()
        vars["showBackToSubmitted"] = isinstance(self._abstract.getCurrentStatus(), review.AbstractStatusWithdrawn)
        #for author in self._abstract.getAuthorList():
        #    if self._abstract.isPrimaryAuthor( author ):
        #        primary_authors.append( self._getAuthorHTML( author ) )
        #    else:
        #        co_authors.append( self._getAuthorHTML( author ) )
        primary_authors = []
        for author in self._abstract.getPrimaryAuthorList():
            primary_authors.append( self._getAuthorHTML( author ) )
        co_authors = []
        for author in self._abstract.getCoAuthorList():
            co_authors.append( self._getAuthorHTML( author ) )
        vars["primary_authors"] = "<br>".join( primary_authors )
        vars["co_authors"] = "<br>".join( co_authors )
        speakers = []
        for spk in self._abstract.getSpeakerList():
            speakers.append(self._getAuthorHTML(spk))
        vars["speakers"] = "<br>".join( speakers )
        vars["tracks"] = self._getTracksHTML()
        vars["type"] = ""
        if self._abstract.getContribType() is not None:
            vars["type"] = self._abstract.getContribType().getName()
        vars["submitter"] = self._getAuthorHTML(self._abstract.getSubmitter())
        vars["submitDate"] = self._abstract.getSubmissionDate().strftime("%d %B %Y %H:%M")
        vars["modificationDate"] = self._abstract.getModificationDate().strftime("%d %B %Y %H:%M")
        vars["disable"],vars["dupDisable"],vars["mergeDisable"] = "","",""
        if self._abstract.getCurrentStatus().__class__ in [review.AbstractStatusAccepted,review.AbstractStatusRejected,review.AbstractStatusWithdrawn]:
            vars["disable"] = "disabled"
            vars["mergeDisable"] = "disabled"
            vars["dupDisable"] = "disabled"

        vars["duplicatedButton"] = _("mark as duplicated")
        vars["duplicateURL"]=quoteattr(str(urlHandlers.UHAbstractModMarkAsDup.getURL(self._abstract)))
        if self._abstract.getCurrentStatus().__class__ == review.AbstractStatusDuplicated:
            vars["duplicatedButton"] = _("unmark as duplicated")
            vars["duplicateURL"]=quoteattr(str(urlHandlers.UHAbstractModUnMarkAsDup.getURL(self._abstract)))
            vars["mergeDisable"] = "disabled"
            vars["disable"] = "disabled"

        vars["mergeButton"] = _("merge into")
        vars["mergeIntoURL"]=quoteattr(str(urlHandlers.UHAbstractModMergeInto.getURL(self._abstract)))
        if self._abstract.getCurrentStatus().__class__ == review.AbstractStatusMerged:
            vars["mergeIntoURL"]=quoteattr(str(urlHandlers.UHAbstractModUnMerge.getURL(self._abstract)))
            vars["mergeButton"] = _("unmerge")
            vars["dupDisable"] = "disabled"
            vars["disable"] = "disabled"

        vars["mergeFrom"] = self._getMergeFromHTML()

        vars["abstractListURL"] = quoteattr( str( urlHandlers.UHConfAbstractManagment.getURL( self._conf ) ) )
        vars["viewTrackDetailsURL"] = quoteattr( str (urlHandlers.UHAbstractTrackProposalManagment.getURL( self._abstract) ) )
        vars["comments"] = self._abstract.getComments()
        vars["abstractId"] = self._abstract.getId()
        vars["contribution"] = self._getContributionHTML()
        vars["abstractPDF"]=urlHandlers.UHAbstractConfManagerDisplayPDF.getURL(self._abstract)
        vars["printIconURL"]=Config.getInstance().getSystemIconURL("pdf")
        vars["abstractXML"]=urlHandlers.UHAbstractToXML.getURL(self._abstract)
        vars["xmlIconURL"]=Config.getInstance().getSystemIconURL("xml")
        vars["acceptURL"]=quoteattr(str(urlHandlers.UHAbstractManagmentAccept.getURL(self._abstract)))
        vars["rejectURL"]=quoteattr(str(urlHandlers.UHAbstractManagmentReject.getURL(self._abstract)))
        vars["changeTrackURL"]=quoteattr(str(urlHandlers.UHAbstractManagmentChangeTrack.getURL(self._abstract)))
        vars["backToSubmittedURL"]=quoteattr(str(urlHandlers.UHAbstractManagmentBackToSubmitted.getURL(self._abstract)))
        vars["modDataURL"]=quoteattr(str(urlHandlers.UHAbstractModEditData.getURL(self._abstract)))
        vars["changeSubmitterURL"]=quoteattr(str(urlHandlers.UHAbstractChangeSubmitter.getURL(self._abstract)))
        vars["propToAccURL"]=quoteattr(str(urlHandlers.UHConfModAbstractPropToAcc.getURL(self._abstract)))
        vars["propToRejURL"]=quoteattr(str(urlHandlers.UHConfModAbstractPropToRej.getURL(self._abstract)))
        vars["withdrawURL"]=quoteattr(str(urlHandlers.UHConfModAbstractWithdraw.getURL(self._abstract)))
        vars["disableWithdraw"]=""
        if self._abstract.getCurrentStatus().__class__ not in \
                [review.AbstractStatusSubmitted,review.AbstractStatusAccepted,
                review.AbstractStatusInConflict,\
                review.AbstractStatusUnderReview,\
                review.AbstractStatusProposedToReject,\
                review.AbstractStatusProposedToAccept]:
            vars["disableWithdraw"]=" disabled"

        rating = self._abstract.getRating()
        if rating == None:
            vars["rating"] = ""
        else:
            vars["rating"] = "%.2f" % rating
        vars["scaleLower"] = self._abstract.getConference().getConfAbstractReview().getScaleLower()
        vars["scaleHigher"] = self._abstract.getConference().getConfAbstractReview().getScaleHigher()
        vars["attachments"] = fossilize(self._abstract.getAttachments().values(), ILocalFileAbstractMaterialFossil)

        return vars


class WPAbstractManagment(WPAbstractManagementBase):

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):
        wc = WAbstractManagment( self._getAW(), self._target )
        return wc.getHTML( params )


class WPAbstractSelectSubmitter(WPAbstractManagementBase):

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WUserSelection( urlHandlers.UHAbstractChangeSubmitter.getURL(), False, forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHAbstractSetSubmitter.getURL()
        return wc.getHTML( params )


class WPModEditData(WPAbstractManagment):

    def __init__(self, rh, abstract, abstractData):
        WPAbstractManagment.__init__(self, rh, abstract)

    def _getTabContent(self,params):
        params["postURL"] = urlHandlers.UHAbstractModEditData.getURL(self._abstract)
        params["origin"] = "management"
        wc = WAbstractDataModification(self._conf)
        return wc.getHTML(params)


class WAbstractManagmentAccept( wcomponents.WTemplated ):

    def __init__( self, aw, abstract ):
        self._abstract = abstract
        self._aw = aw
        self._conf = abstract.getOwner().getOwner()

    def _getTypeItemsHTML( self ):
        items = [ i18nformat("""<option value="not_defined">--_("not defined")--</option>""")]
        status = self._abstract.getCurrentStatus()
        isPropToAcc = isinstance(status, review.AbstractStatusProposedToAccept)
        for type in self._conf.getContribTypeList():
            title,default = type.getName(), ""
            if isPropToAcc and status.getType() == type:
                title = "[*] %s"%title
                default = " selected"
            items.append( """<option value=%s%s>%s</option>"""%(\
                        quoteattr(type.getId()), default, self.htmlText(title)))
        return items

    def _getTrackItemsHTML( self ):
        items = [ i18nformat("""<option value="conf">--_("no track")--</option>""")]
        for track in self._conf.getTrackList():
            #the indicator legend:
            #   [*] -> suggested for that track
            #   [A] -> track proposed to accept
            #   [R] -> track proposed to reject
            indicator, selected = "", ""
            if self._abstract.hasTrack( track ):
                indicator = "[*] "
                jud = self._abstract.getTrackJudgement( track )
                if isinstance(jud, review.AbstractAcceptance):
                    if self._abstract.getCurrentStatus().__class__ == review.AbstractStatusProposedToAccept:
                        selected = " selected"
                    indicator = "[A] "
                elif isinstance(jud, review.AbstractRejection):
                    indicator = "[R] "
            items.append("""<option value="%s"%s>%s%s</option>"""%(track.getId(), selected, indicator, track.getTitle()))
        return items

    def _getSessionItemsHTML( self ):
        items = [ i18nformat("""<option value="conf">--_("no session")--</option>""")]
        for session in self._conf.getSessionList():
            items.append("""<option value="%s">%s</option>"""%(session.getId(), session.getTitle()))
        return items

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractName"] = self._abstract.getTitle()
        vars["tracks"] = "".join( self._getTrackItemsHTML() )
        vars["sessions"] = "".join( self._getSessionItemsHTML() )
        vars["types"] = "".join( self._getTypeItemsHTML() )
        vars["acceptURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentAccept.getURL(self._abstract)))
        vars["cancelURL"] = quoteattr(str(urlHandlers.UHAbstractManagment.getURL(self._abstract)))
        return vars

class WAbstractManagmentAcceptMultiple( wcomponents.WTemplated):

    def __init__( self, abstracts ):
        wcomponents.WTemplated.__init__(self)
        self._abstracts = abstracts
        # we suppose that we always have a least one abstract:
        self._conf = abstracts[0].getOwner().getOwner()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractsQuantity"] = len(self._abstracts)
        vars["tracks"] = self._conf.getTrackList()
        vars["sessions"] = self._conf.getSessionList()
        vars["types"] = self._conf.getContribTypeList()
        vars["listOfAbstracts"] = []
        acceptURL = urlHandlers.UHAbstractManagmentAcceptMultiple.getURL(self._conf)
        IDs = []
        for abstract in self._abstracts:
            IDs.append(abstract.getId())
            vars["listOfAbstracts"].append("[%s] %s"%(abstract.getId(), abstract.getTitle()))
        acceptURL.addParams({'abstracts':IDs})
        vars["acceptURL"] = quoteattr(str(acceptURL))
        vars["cancelURL"] = quoteattr(str(urlHandlers.UHConfAbstractManagment.getURL(self._conf)))
        return vars

class WPAbstractManagmentAccept(WPAbstractManagment):

    def _getTabContent( self, params ):
        wc = WAbstractManagmentAccept( self._getAW(), self._target )
        return wc.getHTML()

class WPAbstractManagmentAcceptMultiple(WPConferenceModifAbstractBase):

    def __init__( self, rh, abstracts ):
        WPConferenceModifAbstractBase.__init__(self, rh, abstracts[0].getConference())
        self._abstracts = abstracts

    def _getPageContent( self, params ):
        wc = WAbstractManagmentAcceptMultiple( self._abstracts )
        return wc.getHTML()


class WPAbstractManagmentRejectMultiple(WPConferenceModifAbstractBase):

    def __init__( self, rh, abstracts ):
        WPConferenceModifAbstractBase.__init__(self, rh, abstracts[0].getConference())
        self._abstracts = abstracts

    def _getPageContent( self, params ):
        wc = WAbstractManagmentRejectMultiple( self._abstracts )
        return wc.getHTML()


class WAbsModAcceptConfirmation(wcomponents.WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["track"]=quoteattr(vars["track"])
        vars["comments"]=quoteattr(vars["comments"])
        vars["type"]=quoteattr(vars["type"])
        vars["acceptURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentAccept.getURL(self._abstract)))
        vars["cancelURL"] = quoteattr(str(urlHandlers.UHAbstractManagment.getURL(self._abstract)))
        return vars


class WPModAcceptConfirmation(WPAbstractManagment):

    def _getTabContent(self,params):
        wc = WAbsModAcceptConfirmation(self._target)
        p={"track":params["track"],
           "session":params["session"],
            "comments":params["comments"],
            "type":params["type"]}
        return wc.getHTML(p)


class WAbsModRejectConfirmation(wcomponents.WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["comments"]=quoteattr(vars["comments"])
        vars["rejectURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentReject.getURL(self._abstract)))
        vars["cancelURL"] = quoteattr(str(urlHandlers.UHAbstractManagment.getURL(self._abstract)))
        return vars


class WPModRejectConfirmation(WPAbstractManagment):

    def _getTabContent(self,params):
        wc = WAbsModRejectConfirmation(self._target)
        p={ "comments":params["comments"] }
        return wc.getHTML(p)


class WAbstractManagmentReject( wcomponents.WTemplated ):

    def __init__( self, aw, abstract ):
        self._abstract = abstract
        self._aw = aw
        self._conf = abstract.getOwner().getOwner()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractName"] = self._abstract.getTitle()
        vars["rejectURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentReject.getURL(self._abstract)))
        vars["cancelURL"] = quoteattr(str(urlHandlers.UHAbstractManagment.getURL(self._abstract)))
        return vars


class WAbstractManagmentRejectMultiple( wcomponents.WTemplated ):

    def __init__( self, abstracts ):
        self._abstracts = abstracts
        # we suppose that we always have a least one abstract:
        self._conf = abstracts[0].getOwner().getOwner()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractsQuantity"] = len(self._abstracts)
        vars["listOfAbstracts"] = []
        rejectURL = urlHandlers.UHAbstractManagmentRejectMultiple.getURL(self._conf)
        IDs = []
        for abstract in self._abstracts:
            IDs.append(abstract.getId())
            vars["listOfAbstracts"].append("[%s] %s"%(abstract.getId(), abstract.getTitle()))
        rejectURL.addParams({'abstracts':IDs})
        vars["rejectURL"] = quoteattr(str(rejectURL))
        vars["cancelURL"] = quoteattr(str(urlHandlers.UHConfAbstractManagment.getURL(self._conf)))
        return vars

class WPAbstractManagmentReject(WPAbstractManagment):

    def _getTabContent( self, params ):
        wc = WAbstractManagmentReject( self._getAW(), self._target )
        return wc.getHTML( params )


class WPModMarkAsDup(WPAbstractManagment):

    def _getTabContent( self, params ):
        wc = wcomponents.WAbstractModMarkAsDup(self._target)
        p={"comments":params.get("comments",""),
            "id":params.get("originalId",""),
            "errorMsg":params.get("errorMsg",""),
            "duplicateURL":urlHandlers.UHAbstractModMarkAsDup.getURL(self._abstract),
            "cancelURL":urlHandlers.UHAbstractManagment.getURL(self._abstract)}
        return wc.getHTML(p)


class WPModUnMarkAsDup(WPAbstractManagment):

    def _getTabContent( self, params ):
        wc = wcomponents.WAbstractModUnMarkAsDup(self._target)
        p={ "comments":params.get("comments",""),
            "unduplicateURL":urlHandlers.UHAbstractModUnMarkAsDup.getURL(self._abstract),
            "cancelURL":urlHandlers.UHAbstractManagment.getURL(self._abstract)}
        return wc.getHTML(p)


class WAbstractModMergeInto(wcomponents.WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract

    def _getErrorHTML(self,msg):
        if msg.strip()=="":
            return ""
        return """
                <tr align="center">
                    <td colspan="2">
                        <table align="center" valign="middle" style="padding:10px; border:1px solid #5294CC; background:#F6F6F6">
                            <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td><font color="red">%s</font></td>
                                <td>&nbsp;</td>
                            </tr>
                            <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                        </table>
                    </td>
                </tr>
                <tr><td>&nbsp;</td></tr>
                """%self.htmlText(msg)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["mergeURL"]=quoteattr(str(vars["mergeURL"]))
        vars["cancelURL"]=quoteattr(str(vars["cancelURL"]))
        vars["error"]=self._getErrorHTML(vars.get("errorM",""))
        vars["includeAuthorsChecked"]=""
        if vars.get("includeAuthors",False):
            vars["includeAuthorsChecked"]=" checked"
        vars["notifyChecked"]=""
        if vars.get("doNotify",False):
            vars["notifyChecked"]=" checked"
        return vars


class WPModMergeInto(WPAbstractManagment):

    def _getTabContent( self, params ):
        wc=WAbstractModMergeInto(self._target)
        p={"cancelURL":urlHandlers.UHAbstractManagment.getURL(self._abstract),\
            "mergeURL":urlHandlers.UHAbstractModMergeInto.getURL(self._abstract),\
            "comments":params.get("comments",""),\
            "id":params.get("targetId",""),\
            "errorM":params.get("errorMsg",""),\
            "includeAuthors":params.get("includeAuthors",False),
            "doNotify":params.get("notify",False)}
        return wc.getHTML(p)


class WAbstractModUnMerge(wcomponents.WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["unmergeURL"]=quoteattr(str(vars["unmergeURL"]))
        vars["cancelURL"]=quoteattr(str(vars["cancelURL"]))
        return vars


class WPModUnMerge(WPAbstractManagment):

    def _getTabContent( self, params ):
        wc = WAbstractModUnMerge(self._target)
        p={ "comments":params.get("comments",""),
            "unmergeURL":urlHandlers.UHAbstractModUnMerge.getURL(self._abstract),
            "cancelURL":urlHandlers.UHAbstractManagment.getURL(self._abstract)}
        return wc.getHTML(p)


class WConfModAbstractPropToAcc(wcomponents.WTemplated):

    def __init__(self,aw,abstract):
        self._abstract=abstract
        self._aw=aw

    def _getTracksHTML(self):
        res=[]
        for track in self._abstract.getTrackListSorted():
            u=self._aw.getUser()
            if not self._abstract.canUserModify(u) and \
                                            not track.canUserCoordinate(u):
                continue
            id=quoteattr(str(track.getId()))
            legend=""
            jud=self._abstract.getTrackJudgement(track)
            if isinstance(jud,review.AbstractAcceptance):
                legend="[PA]"
            elif isinstance(jud,review.AbstractRejection):
                legend="[PR]"
            elif isinstance(jud,review.AbstractReallocation):
                legend="[PM]"
            caption="%s%s"%(legend,self.htmlText(track.getTitle()))
            res.append("""<option value=%s>%s</option>"""%(id,caption))
        return "".join(res)

    def _getContribTypesHTML(self):
        res=["""<option value="">--none--</option>"""]
        for cType in self._abstract.getConference().getContribTypeList():
            id=quoteattr(str(cType.getId()))
            caption=self.htmlText(cType.getName())
            res.append("""<option value=%s>%s</option>"""%(id,caption))
        return res

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModAbstractPropToAcc.getURL(self._abstract)))
        vars["tracks"]=self._getTracksHTML()
        vars["contribTypes"]=self._getContribTypesHTML()
        vars["comment"]=""
        vars["changeTrackURL"]=quoteattr(str(urlHandlers.UHAbstractManagmentChangeTrack.getURL(self._abstract)))
        vars["abstractReview"] = self._abstract.getConference().getConfAbstractReview()

        return vars


class WPModPropToAcc(WPAbstractManagment):

    def _getTabContent( self, params ):
        wc=WConfModAbstractPropToAcc(self._rh.getAW(),self._abstract)
        return wc.getHTML()

class WConfModAbstractPropToRej(wcomponents.WTemplated):

    def __init__(self,aw,abstract):
        self._abstract=abstract
        self._aw=aw

    def _getTracksHTML(self):
        res=[]
        u=self._aw.getUser()
        for track in self._abstract.getTrackListSorted():
            if not self._abstract.canUserModify(u) and \
                                            not track.canUserCoordinate(u):
                continue
            id=quoteattr(str(track.getId()))
            legend=""
            jud=self._abstract.getTrackJudgement(track)
            if isinstance(jud,review.AbstractAcceptance):
                legend="[PA]"
            elif isinstance(jud,review.AbstractRejection):
                legend="[PR]"
            elif isinstance(jud,review.AbstractReallocation):
                legend="[PM]"
            caption="%s%s"%(legend,self.htmlText(track.getTitle()))
            res.append("""<option value=%s>%s</option>"""%(id,caption))
        return "".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModAbstractPropToRej.getURL(self._abstract)))
        vars["tracks"]=self._getTracksHTML()
        vars["comment"]=""
        vars["changeTrackURL"]=quoteattr(str(urlHandlers.UHAbstractManagmentChangeTrack.getURL(self._abstract)))
        vars["abstractReview"] = self._abstract.getConference().getConfAbstractReview()
        return vars


class WPModPropToRej(WPAbstractManagment):

    def _getTabContent( self, params ):
        wc=WConfModAbstractPropToRej(self._rh.getAW(),self._abstract)
        return wc.getHTML()


class WAbstractManagmentChangeTrack( wcomponents.WTemplated ):

    def __init__( self, aw, abstract ):
        self._abstract = abstract
        self._aw = aw
        self._conf = abstract.getOwner().getOwner()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractName"] = self._abstract.getTitle()
        tracks = ""
        for track in self._conf.getTrackList():
            checked = ""
            if self._abstract.hasTrack( track ):
                checked = "checked"
            tracks += "<input %s name=\"tracks\" type=\"checkbox\" value=\"%s\"> %s<br>\n"%(checked,track.getId(), track.getTitle())
        vars["tracks"] = tracks
        return vars


class WPAbstractManagmentChangeTrack(WPAbstractManagementBase):

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):
        wc = WAbstractManagmentChangeTrack( self._getAW(), self._target )
        params["saveURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentChangeTrack.getURL(self._abstract)))
        params["cancelURL"] = quoteattr(str(urlHandlers.UHAbstractManagment.getURL(self._abstract)))
        return wc.getHTML( params )


class WAbstractTrackManagment(wcomponents.WTemplated):

    def __init__( self, aw, abstract ):
        self._abstract = abstract
        self._aw = aw
        self._conf = abstract.getOwner().getOwner()

    def _getResponsibleHTML( self, track, res ):
        tmp = "%s (%s)"%(res.getFullName(), res.getAffiliation())
        tmp = self.htmlText( tmp )
        if res.getEmail() != "":
            mailtoSubject = _("[%s] Abstract %s: %s")%( self._conf.getTitle(), self._abstract.getId(), self._abstract.getTitle() )
            mailtoBody=""
            if track is not None:
                mailtoBody = _("You can access the abstract at [%s]")%str( urlHandlers.UHTrackAbstractModif.getURL( track, self._abstract ) )
            mailtoURL = "mailto:%s?subject=%s&body=%s"%( res.getEmail(), \
                                            urllib.quote( mailtoSubject ), \
                                            urllib.quote( mailtoBody ) )
            href = quoteattr( mailtoURL )
            tmp = """<a href=%s><font size=\"-2\">%s</font></a>"""%(href, tmp)
        return tmp

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tracks = ""

        tzUtil = DisplayTZ(self._aw,self._conf)
        tz = tzUtil.getDisplayTZ()
        judgements = False # this var shows if there is any judgement to show in the table

        for track in self._abstract.getTrackListSorted():
            firstJudg=True
            for status in self._abstract.getJudgementHistoryByTrack(track):
                judgements = True
                if status.__class__ == review.AbstractAcceptance:
                    contribType = ""
                    if status.getContribType() is not None:
                        contribType = "(%s)"%status.getContribType().getName()
                    st = _("Proposed to accept %s")%(self.htmlText(contribType))
                    color = "#D2FFE9"
                    modifDate = getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M")
                    modifier = self._getResponsibleHTML( track, status.getResponsible() )
                    comments = status.getComment()
                elif status.__class__ == review.AbstractRejection:
                    st = _("Proposed to reject")
                    color = "#FFDDDD"
                    modifDate = getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M")
                    modifier = self._getResponsibleHTML( track, status.getResponsible() )
                    comments = status.getComment()
                elif status.__class__ == review.AbstractReallocation:
                    l = []
                    for propTrack in status.getProposedTrackList():
                        l.append( self.htmlText( propTrack.getTitle() ) )
                    st = i18nformat(""" _("Proposed for other tracks"):<font size="-1"><table style="padding-left:10px"><tr><td>%s</td></tr></table></font>""")%"<br>".join(l)
                    color = "#F6F6F6"
                    modifDate = getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M")
                    modifier = self._getResponsibleHTML( track, status.getResponsible() )
                    comments = status.getComment()
                elif status.__class__ == review.AbstractMarkedAsDuplicated:
                    st = _("""Marked as duplicated: original abstract has id '%s'""")%(status.getOriginalAbstract().getId())
                    color = "#DDDDFF"
                    modifDate = getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M")
                    modifier = self._getResponsibleHTML( track, status.getResponsible() )
                    comments = status.getComment()
                elif status.__class__ == review.AbstractUnMarkedAsDuplicated:
                    st = _("""Unmarked as duplicated""")
                    color = "#FFFFCC"
                    modifDate = getAdjustedDate(status.getDate(),tz=tz).strftime("%d %B %Y %H:%M")
                    modifier = self._getResponsibleHTML( track, status.getResponsible() )
                    comments = status.getComment()
                else:
                    st = "&nbsp;"
                    color = "white"
                    modifDate = "&nbsp;"
                    modifier = "&nbsp;"
                    comments = "&nbsp;"
                trackTitle = _("General Judgment")
                if track is not None and firstJudg:
                    trackTitle = track.getTitle()
                if firstJudg:
                    firstJudg=False
                else:
                    trackTitle="&nbsp;"
                if status.getJudValue() == None:
                    # There were no questions when the abstract was judgement, the value 0 is wrong for this case
                    # because it is possible to have answered questions and a final value of 0.
                    rating = "-"
                    detailsImg = ""
                else:
                    # Get the list of questions and the answers values
                    questionNames = []
                    answerValues = []
                    answers = status.getAnswers()
                    for ans in answers:
                        questionNames.append(ans.getQuestion().getText())
                        answerValues.append("%.2f" % ans.getValue())
                    rating = "%.2f" % status.getJudValue()
                    total = "%.2f" % status.getTotalJudValue()
                    imgIcon = Configuration.Config.getInstance().getSystemIconURL("itemCollapsed")
                    detailsImg = """<img src="%s" onClick = "showQuestionDetails(%s,%s,%s,%s)" style="cursor: pointer;">"""% (imgIcon, questionNames, answerValues, rating, total)

                tracks += "<tr bgcolor=\"%s\">"%color
                tracks += "<td nowrap class=\"blacktext\" style=\"padding-right:10px;background-color:white\"><b>&nbsp;%s</b></td>"%(trackTitle)
                tracks += "<td nowrap class=\"blacktext\" style=\"padding-right:10px\">&nbsp;%s</td>"%st
                tracks += "<td nowrap class=\"blacktext\" style=\"padding-right:10px\">&nbsp;%s</td>"%modifier
                tracks += "<td nowrap class=\"blacktext\" style=\"padding-right:10px\"><font size=\"-2\">&nbsp;%s</font></td>"%modifDate
                tracks += "<td nowrap class=\"blacktext\" style=\"padding-right:10px\">&nbsp;%s&nbsp;%s</td>"%(rating, detailsImg)
                tracks += """<td class=\"blacktext\">&nbsp;%s</td>"""%comments
                tracks += "</tr>"

            if self._abstract.getJudgementHistoryByTrack(track) != []:
                tracks+="""
                        <tr><td>&nbsp;</td></tr>
                        """
        if self._abstract.getRating():
            vars["ratingAverage"] = "%.2f" % self._abstract.getRating()
        else:
            vars["ratingAverage"] = None
        vars["judgements"] = judgements
        vars["tracks"] = tracks
        vars["scaleLower"] = self._conf.getConfAbstractReview().getScaleLower()
        vars["scaleHigher"] = self._conf.getConfAbstractReview().getScaleHigher()
        return vars


class WPAbstractTrackManagment(WPAbstractManagementBase):

    def _setActiveTab( self ):
        self._tabTracks.setActive()
        self._subTabTrack.setActive()

    def _getTabContent( self, params ):
        wc = WAbstractTrackManagment( self._getAW(), self._target )
        return wc.getHTML( params )


class WAbstractTrackOrderByRating(wcomponents.WTemplated):

    def __init__( self, aw, abstract ):
        self._abstract = abstract
        self._conf = abstract.getOwner().getOwner()

    def getVars( self ):
        questionIds = self._abstract.getQuestionsAverage().keys()
        answerValues = self._abstract.getQuestionsAverage().values()
        i = 0
        questions = {}
        for qText in questionIds:
            questions[qText] = "%.2f" % answerValues[i]
            i += 1
        vars = wcomponents.WTemplated.getVars( self )

        vars["questions"] = questions
        if self._abstract.getRating():
            vars["ratingAverage"] = "%.2f" % self._abstract.getRating()
        else:
            vars["ratingAverage"] = None
        vars["scaleLower"] = self._conf.getConfAbstractReview().getScaleLower()
        vars["scaleHigher"] = self._conf.getConfAbstractReview().getScaleHigher()
        return vars


class WPAbstractTrackOrderByRating(WPAbstractManagementBase):

    def _setActiveTab( self ):
        self._tabTracks.setActive()
        self._subTabRating.setActive()

    def _getTabContent( self, params ):
        wc = WAbstractTrackOrderByRating( self._getAW(), self._target )
        return wc.getHTML( params )


class WAbstractModAC(wcomponents.WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["subCanModURL"]=quoteattr("")
        vars["subCanModStatus"]=self.htmlText()
        vars["subCanModBtnName"]=quoteattr("")
        vars["subCanModBtnCaption"]=quoteattr("")
        return vars


class WPModAC(WPAbstractManagementBase):

    def _setActiveTab( self ):
        self._tabAC.setActive()

    def _getTabContent( self, params ):
        wc=WAbstractModAC(self._target)
        return wc.getHTML()


class WPModIntComments(WPAbstractManagementBase):

    def _setActiveTab( self ):
        self._tabComments.setActive()

    def _getTabContent( self, params ):
        wc=wcomponents.WAbstractModIntComments(self._getAW(),self._target)
        p={"newCommentURL":urlHandlers.UHAbstractModNewIntComment.getURL(self._abstract),
            "commentEditURLGen":urlHandlers.UHAbstractModIntCommentEdit.getURL,
            "commentRemURLGen":urlHandlers.UHAbstractModIntCommentRem.getURL
        }
        return wc.getHTML(p)


class WPModNewIntComment(WPModIntComments):

    def _getTabContent( self, params ):
        wc=wcomponents.WAbstractModNewIntComment(self._getAW(),self._target)
        p={"postURL":urlHandlers.UHAbstractModNewIntComment.getURL(self._abstract)}
        return wc.getHTML(p)


class WPModIntCommentEdit(WPModIntComments):

    def __init__(self,rh,comment):
        self._comment=comment
        WPModIntComments.__init__(self,rh,comment.getAbstract())

    def _getTabContent( self, params ):
        wc=wcomponents.WAbstractModIntCommentEdit(self._comment)
        p={"postURL": urlHandlers.UHAbstractModIntCommentEdit.getURL(self._comment)}
        return wc.getHTML(p)


class WAbstractModNotifLog(wcomponents.WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract

    def _getResponsibleHTML( self, res ):
        conf=self._abstract.getConference()
        tmp = "%s (%s)"%(res.getFullName(), res.getAffiliation())
        tmp = self.htmlText( tmp )
        if res.getEmail() != "":
            mailtoSubject = _("[%s] Abstract %s: %s")%( conf.getTitle(), self._abstract.getId(), self._abstract.getTitle() )
            mailtoURL = "mailto:%s?subject=%s"%( res.getEmail(), \
                                            urllib.quote( mailtoSubject ))
            href = quoteattr( mailtoURL )
            tmp = """<a href=%s>%s</a>"""%(href, tmp)
        return tmp

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        res=[]
        for entry in self._abstract.getNotificationLog().getEntryList():
            d=entry.getDate().strftime("%Y-%m-%d %H:%M")
            resp=entry.getResponsible()
            tplCaption=entry.getTpl().getName()
            tplLink= i18nformat("""
                    <b>%s</b> <font color="red"> _("(This template doesn't exist anymore)")</font>
                    """)%tplCaption
            if entry.getTpl().getOwner() is not None:
                url=urlHandlers.UHAbstractModNotifTplDisplay.getURL(entry.getTpl())
                tplLink="<a href=%s>%s</a>"%(quoteattr(str(url)),self.htmlText(tplCaption))
            res.append( i18nformat("""
                        <tr>
                            <td bgcolor="white">
                                %s _("by") %s
                                <br>
                                _("notification template used"): %s
                            </td>
                        </tr>
                        """)%(self.htmlText(d),self._getResponsibleHTML(resp),tplLink))
        vars["entries"]="".join(res)
        return vars


class WPModNotifLog(WPAbstractManagementBase):

    def _setActiveTab( self ):
        self._tabNotifLog.setActive()

    def _getTabContent( self, params ):
        wc=WAbstractModNotifLog(self._target)
        return wc.getHTML()


class WConfModAbstractWithdraw(wcomponents.WTemplated):

    def __init__(self,aw,abstract):
        self._abstract=abstract
        self._aw=aw

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHConfModAbstractWithdraw.getURL(self._abstract)))
        vars["comment"]=""
        return vars


class WPModWithdraw(WPAbstractManagment):

    def _getTabContent( self, params ):
        wc=WConfModAbstractWithdraw(self._rh.getAW(),self._abstract)
        return wc.getHTML()

class WAbstractModifTool(wcomponents.WTemplated):

    def __init__( self, contrib ):
        self._contrib = contrib

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["deleteIconURL"] = Config.getInstance().getSystemIconURL("delete")
        return vars

class WPModTools( WPAbstractManagment ):

    def _setActiveTab( self ):
        self._tabTools.setActive()

    def _getTabContent( self, params ):
        wc = WAbstractModifTool( self._target )
        pars = { \
            "deleteContributionURL": urlHandlers.UHAbstractDelete.getURL( self._target )
                }
        return wc.getHTML( pars )

class WPModRemConfirmation(WPModTools):

    def __init__(self,rh,abs):
        WPAbstractManagment.__init__(self,rh,abs)
        self._abs=abs

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        msg= _("""Are you sure you want to delete the abstract "%s"?""")%(self._abs.getTitle())
        url=urlHandlers.UHAbstractDelete.getURL(self._abs)
        return wc.getHTML(msg,url,{})
