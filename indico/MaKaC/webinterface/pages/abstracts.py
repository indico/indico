# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
from flask import session

from xml.sax.saxutils import quoteattr
import urllib
from pytz import timezone

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.navigation as navigation
import MaKaC.review as review
from MaKaC.webinterface.pages.conferences import WPConferenceModifBase, WPConferenceDefaultDisplayBase, WPConferenceModifAbstractBase
from MaKaC.webinterface.pages.conferences import WConfDisplayBodyBase
from indico.core.config import Config
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from indico.util.date_time import format_time, format_date, format_datetime
from MaKaC.common.timezoneUtils import nowutc, getAdjustedDate, DisplayTZ
from indico.core import config as Configuration
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.conference import ILocalFileAbstractMaterialFossil
from MaKaC.review import AbstractStatusSubmitted
from MaKaC.review import AbstractTextField
from MaKaC.common.TemplateExec import render

from indico.util.string import render_markdown


class WConfCFADeactivated(WConfDisplayBodyBase):

    _linkname = "CFA"

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        return wvars


class WPCFAInactive(WPConferenceDefaultDisplayBase):

    def _getBody(self, params):
        wc = WConfCFADeactivated(self._getAW(), self._conf)
        return wc.getHTML()


class WCFANotYetOpened(WConfDisplayBodyBase):

    _linkname = "SubmitAbstract"

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def getVars(self):
        cfaMgr = self._conf.getAbstractMgr()
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["start_date"] = format_date(cfaMgr.getStartSubmissionDate(), "long")
        return wvars


class WPCFANotYetOpened(WPConferenceDefaultDisplayBase):

    def _getBody(self, params):
        wc = WCFANotYetOpened(self._getAW(), self._conf)
        return wc.getHTML()

    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._cfaNewSubmissionOpt)


class WCFAClosed(WConfDisplayBodyBase):

    _linkname = "SubmitAbstract"

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def getVars(self):
        cfaMgr = self._conf.getAbstractMgr()
        wvars = wcomponents.WTemplated.getVars(self)
        wvars["body_title"] = self._getTitle()
        wvars["end_date"] = format_date(cfaMgr.getEndSubmissionDate(), "long")
        return wvars


class WPCFAClosed(WPConferenceDefaultDisplayBase):

    def __init__(self, rh, conf, is_modif):
        WPConferenceDefaultDisplayBase.__init__(self, rh, conf)
        self._is_modif = is_modif

    def _getBody(self, params):
        wc = WCFAClosed(self._getAW(), self._conf)
        return wc.getHTML({'is_modif': self._is_modif})

    def _defineSectionMenu(self):
        WPConferenceDefaultDisplayBase._defineSectionMenu(self)
        self._sectionMenu.setCurrentItem(self._cfaNewSubmissionOpt)


class WConfCFA(WConfDisplayBodyBase):

    _linkname = "CFA"

    def __init__(self, aw, conf):
        self._conf = conf
        self._aw = aw

    def _getActionsHTML(self):
        html = ""
        cfa = self._conf.getAbstractMgr()
        if nowutc() < cfa.getStartSubmissionDate():
            return html
        else:
            submitOpt = ""
            if cfa.inSubmissionPeriod():
                submitOpt = i18nformat("""<li><a href="%s"> _("Submit a new abstract")</a></li>""") % (
                    urlHandlers.UHAbstractSubmission.getURL(self._conf))
            html = i18nformat("""
            <b> _("Possible actions you can carry out"):</b>
            <ul>
                %s
                <li><a href="%s"> _("View or modify your already submitted abstracts")</a></li>
            </ul>
                   """) % (submitOpt, urlHandlers.UHUserAbstracts.getURL(self._conf))
        return html

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        cfa = self._conf.getAbstractMgr()
        if cfa.inSubmissionPeriod():
            wvars["status"] = _("OPENED")
        else:
            wvars["status"] = _("CLOSED")
        wvars["startDate"] = cfa.getStartSubmissionDate().strftime("%d %B %Y")
        wvars["endDate"] = cfa.getEndSubmissionDate().strftime("%d %B %Y")
        wvars["actions"] = self._getActionsHTML()
        wvars["announcement"] = cfa.getAnnouncement()
        wvars["body_title"] = self._getTitle()
        return wvars


class WPConferenceCFA( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NEConferenceCFA

    def _getBody(self, params):
        wc = WConfCFA(self._getAW(), self._conf)
        return wc.getHTML()

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._cfaOpt)


class WPAbstractSubmission( WPConferenceDefaultDisplayBase ):
    navigationEntry = navigation.NEAbstractSubmission

    def getCSSFiles(self):
        return WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._includeJSPackage('Management') + \
            self._asset_env['abstracts_js'].urls()

    def _getHeadContent(self):
        return WPConferenceDefaultDisplayBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])

    def _getBody( self, params ):
        params["postURL"] = urlHandlers.UHAbstractSubmission.getURL( self._conf )
        params["origin"] = "display"
        wc = WAbstractDataModification( self._conf )
        return wc.getHTML( params )

    def _defineSectionMenu( self ):
        WPConferenceDefaultDisplayBase._defineSectionMenu( self )
        self._sectionMenu.setCurrentItem(self._cfaNewSubmissionOpt)


class WUserAbstracts(WConfDisplayBodyBase):

    _linkname = "ViewAbstracts"

    def __init__(self, aw, conf):
        self._aw = aw
        self._conf = conf

    def _getAbstractStatus(self, abstract):
        status = abstract.getCurrentStatus()
        if isinstance(status, review.AbstractStatusAccepted):
            statusLabel = _("Accepted")
            if status.getType() is not None and status.getType() != "":
                return "%s as %s" % (statusLabel, status.getType().getName())
        elif isinstance(status, review.AbstractStatusRejected):
            return _("Rejected")
        elif isinstance(status, review.AbstractStatusWithdrawn):
            return _("Withdrawn")
        elif isinstance(status, review.AbstractStatusDuplicated):
            return _("Duplicated")
        elif isinstance(status, review.AbstractStatusMerged):
            return _("Merged")
        elif isinstance(status, (review.AbstractStatusProposedToAccept, review.AbstractStatusProposedToReject)):
            return _("Under Review")
        elif isinstance(status, (review.AbstractInConflict)):
            return _("In Conflict")
        return _("Submitted")

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        cfaMgr = self._conf.getAbstractMgr()

        abstracts = cfaMgr.getAbstractListForAvatar(self._aw.getUser())
        abstracts += cfaMgr.getAbstractListForAuthorEmail(self._aw.getUser().getEmail())

        wvars["body_title"] = self._getTitle()
        wvars["abstracts"] = sorted(set(abstracts), key=lambda i: int(i.getId()))
        wvars["formatDate"] = lambda date: format_date(date, "d MMM yyyy")
        wvars["formatTime"] = lambda time: format_time(time, format="short", timezone=timezone(DisplayTZ(self._aw, self._conf).getDisplayTZ()))
        wvars["getAbstractStatus"] = lambda abstract: self._getAbstractStatus(abstract)
        wvars["conf"] = self._conf
        return wvars


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

    def getCSSFiles(self):
        return WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._includeJSPackage('Management') + \
            self._asset_env['abstracts_js'].urls()


class WAbstractCannotBeModified(wcomponents.WTemplated):

    def __init__(self, abstract):
        self._abstract = abstract

    def getVars(self):
        wvars = wcomponents.WTemplated.getVars(self)
        wvars['underReview'] = not isinstance( self._abstract.getCurrentStatus(), AbstractStatusSubmitted)
        return wvars


class WPAbstractCannotBeModified( WPAbstractDisplayBase ):

    def _getBody( self, params ):
        wc = WAbstractCannotBeModified( self._abstract )
        return wc.getHTML()


class WAbstractSubmissionConfirmation(wcomponents.WTemplated):

    def __init__(self, aw, abstract):
        self._aw = aw
        self._abstract = abstract

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["displayURL"] = quoteattr(str(urlHandlers.UHAbstractDisplay.getURL(self._abstract)))
        vars["displayURLText"] = self.htmlText(str(urlHandlers.UHAbstractDisplay.getURL(self._abstract)))
        conf = self._abstract.getConference()
        vars["userAbstractsURL"] = quoteattr(str(urlHandlers.UHUserAbstracts.getURL(conf)))
        vars["userAbstractsURLText"] = self.htmlText(str(urlHandlers.UHUserAbstracts.getURL(conf)))
        vars["CFAURL"] = quoteattr(str(urlHandlers.UHConferenceCFA.getURL(conf)))
        vars["abstractId"] = self._abstract.getId()
        return vars


class WPAbstractSubmissionConfirmation(WPAbstractDisplayBase):
    navigationEntry = navigation.NEAbstractSubmissionConfirmation

    def _getBody(self, params):
        wc = WAbstractSubmissionConfirmation(self._getAW(), self._abstract)
        return wc.getHTML()


class WAbstractDisplay(wcomponents.WTemplated):

    def __init__(self, aw, abstract):
        self._abstract = abstract
        self._aw = aw

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        tzUtil = DisplayTZ(self._aw, self._abstract.getConference())
        tz = tzUtil.getDisplayTZ()

        status = self._abstract.getCurrentStatus()
        if isinstance(status, review.AbstractStatusAccepted):
            vars["contribType"] = status.getType()
            vars["tracks"] = status.getTrack()
        else:
            vars["tracks"] = self._abstract.getTrackListSorted()
            vars["contribType"] = self._abstract.getContribType()
        vars["modifyURL"] = str(urlHandlers.UHAbstractModify.getURL(self._abstract))
        vars["withdrawURL"] = str(urlHandlers.UHAbstractWithdraw.getURL(self._abstract))
        vars["recoverURL"] = str(urlHandlers.UHAbstractRecovery.getURL(self._abstract))

        vars["attachments"] = fossilize(self._abstract.getAttachments().values(), ILocalFileAbstractMaterialFossil)
        vars["abstract"] = self._abstract

        vars["formatDate"] = lambda date: format_date(date, "d MMM yyyy")
        vars["formatTime"] = lambda time: format_time(time, format="short", timezone=timezone(tz))

        vars["modifyDisabled"] = isinstance(status, (review.AbstractStatusAccepted,
                                                     review.AbstractStatusRejected, review.AbstractStatusDuplicated, review.AbstractStatusMerged))
        vars["withdrawDisabled"] = isinstance(status, (review.AbstractStatusAccepted, review.AbstractStatusRejected,
                                                       review.AbstractStatusWithdrawn, review.AbstractStatusDuplicated, review.AbstractStatusMerged))
        status = self._abstract.getCurrentStatus()
        if isinstance(status, review.AbstractStatusAccepted):
            vars["statusText"] = _("ACCEPTED ")
            if status.getType() is not None and status.getType() != "":
                vars["statusText"] += "as %s" % status.getType().getName()
            vars["statusClass"] = "abstractStatusAccepted"
            vars["statusComments"] = ""
        elif isinstance(status, review.AbstractStatusRejected):
            vars["statusText"] = _("REJECTED")
            vars["statusClass"] = "abstractStatusRejected"
            vars["statusComments"] = ""
        elif isinstance(status, review.AbstractStatusWithdrawn):
            vars["statusText"] = _("Withdrawn")
            vars["statusClass"] = "abstractStatusWithdrawn"
            vars["statusComments"] = i18nformat("""_("Withdrawn") by %s _("on") %s %s""") % (self.htmlText(status.getResponsible().getFullName()), format_date(status.getDate(), "d MMM yyyy"), format_time(status.getDate(), format="short", timezone=timezone(tz)))
        elif isinstance(status, review.AbstractStatusDuplicated):
            vars["statusText"] = _("Duplicated")
            vars["statusClass"] = "abstractStatusDuplicated"
            vars["statusComments"] = ""
        elif isinstance(status, review.AbstractStatusMerged):
            vars["statusText"] = _("Merged")
            vars["statusClass"] = "abstractStatusMerged"
            vars["statusComments"] = i18nformat("""_("Merged") into %s-%s""") % (self.htmlText(status.getTargetAbstract().getId()), self.htmlText(status.getTargetAbstract().getTitle()))
        elif isinstance(status, (review.AbstractStatusProposedToAccept, review.AbstractStatusProposedToReject)):
            vars["statusText"] = _("Under Review")
            vars["statusClass"] = "abstractStatusUnderReview"
            vars["statusComments"] = ""
        else:
            vars["statusText"] = _("Submitted")
            vars["statusClass"] = "abstractStatusSubmitted"
            vars["statusComments"] = ""
        vars["accessWrapper"] = self._aw
        return vars


class WPAbstractDisplay(WPAbstractDisplayBase):
    navigationEntry = navigation.NEAbstractDisplay

    def _getHeadContent(self):
        return WPAbstractDisplayBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])

    def _getBody(self, params):
        wc = WAbstractDisplay(self._getAW(), self._abstract)
        return wc.getHTML()


class WAbstractDataModification(WConfDisplayBodyBase):

    _linkname = "SubmitAbstract"

    def __init__(self, conf):
        self._conf = conf
        self._limitedFieldList = []
        self._mandatoryFieldList = []  # all mandatory fields ids, except which are also limited

    def _setMandatoryAndLimitedFields(self):
        abfm = self._conf.getAbstractMgr().getAbstractFieldsMgr()
        for f in abfm.getFields():
            id = f.getId()
            if f.isActive():
                if isinstance(f, AbstractTextField):
                    maxLength = int(f.getMaxLength())
                    limitation = f.getLimitation()
                    if maxLength > 0:  # it means there is a limit for the field in words or in characters
                        self._limitedFieldList.append(["f_"+id, maxLength, "maxLimitionCounter_"+id.replace(" ", "_"), limitation, str(f.isMandatory())])  # append the textarea/input id
                if f.isMandatory():
                    self._mandatoryFieldList.append("f_"+id)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["body_title"] = self._getTitle()
        vars["postURL"] = quoteattr(str(vars["postURL"]))
        vars["origin"] = vars.get("origin", "display")
        vars["abstractTitle"] = quoteattr(str(vars.get("title", "")))
        vars["prAuthors"] = fossilize(vars.get("prAuthors", []))
        vars["coAuthors"] = fossilize(vars.get("coAuthors", []))
        cfaMgr = self._conf.getAbstractMgr()
        vars["tracksMandatory"] = cfaMgr.areTracksMandatory()
        vars["tracks"] = self._conf.getTrackList()
        if cfaMgr.getMultipleTracks():
            vars["trackListType"] = "checkbox"
        else:
            vars["trackListType"] = "radio"
        vars["tracksSelected"] = vars.get("tracksSelectedList", [])  # list of track ids that had been selected
        vars["types"] = self._conf.getContribTypeList()
        vars["typeSelected"] = vars.get("type", None)
        vars["comments"] = str(vars.get("comments", ""))
        fieldDict = {}
        for field in cfaMgr.getAbstractFieldsMgr().getFields():
            f_id = "f_" + field.getId()
            fieldDict[f_id] = vars.get(f_id, "")
        vars["fieldDict"] = fieldDict
        vars["additionalFields"] = cfaMgr.getAbstractFieldsMgr().getFields()
        self._setMandatoryAndLimitedFields()
        vars["limitedFieldList"] = self._limitedFieldList
        vars["mandatoryFieldList"] = self._mandatoryFieldList
        vars["attachedFilesAllowed"] = cfaMgr.canAttachFiles()
        vars["showSelectAsSpeaker"] = cfaMgr.showSelectAsSpeaker()
        vars["isSelectSpeakerMandatory"] = cfaMgr.isSelectSpeakerMandatory()
        #TODO: In case of error we will lose the attached files, we should keep them somehow
        vars["attachments"] = fossilize(vars.get("attachments", []), ILocalFileAbstractMaterialFossil)
        return vars


class WPAbstractModify(WPAbstractDisplayBase):
    navigationEntry = navigation.NEAbstractModify

    def _getHeadContent(self):
        return WPAbstractDisplayBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])

    def getJSFiles(self):
        return WPAbstractDisplayBase.getJSFiles(self) + \
            self._includeJSPackage('Management')

    def getCSSFiles(self):
        return WPAbstractDisplayBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def _getBody(self, params):
        params["postURL"] = urlHandlers.UHAbstractModify.getURL(self._abstract)
        wc = WAbstractDataModification(self._abstract.getConference())
        return wc.getHTML(params)


class WAbstractWithdraw(wcomponents.WTemplated):

    def __init__(self, abstract):
        self._abstract = abstract

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["title"] = self.htmlText(self._abstract.getTitle())
        vars["postURL"] = urlHandlers.UHAbstractWithdraw.getURL(self._abstract)
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

    def _getHeadContent(self):
        return WPConferenceModifBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
            self._asset_env['abstracts_js'].urls()

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()


class WAbstractManagment(wcomponents.WTemplated):

    def __init__(self, aw, abstract):
        self._abstract = abstract
        self._aw = aw
        self._conf = abstract.getOwner().getOwner()

    def _getAuthorHTML(self, auth):
        tmp = "%s (%s)" % (auth.getFullName(), auth.getAffiliation())
        tmp = self.htmlText(tmp)
        if auth.getEmail() != "":
            mailtoSubject = i18nformat("""[%s] _("Abstract") %s: %s""") % (self._conf.getTitle(), self._abstract.getId(), self._abstract.getTitle())
            mailtoURL = "mailto:%s?subject=%s" % (auth.getEmail(), urllib.quote(mailtoSubject))
            href = quoteattr(mailtoURL)
            tmp = """<a href=%s>%s</a>""" % (href, tmp)
        return tmp

    def _getStatusHTML(self):
        status = self._abstract.getCurrentStatus()
        html = """<b>%s</b>""" % AbstractStatusList.getInstance().getCaption(status.__class__).upper()
        tzUtil = DisplayTZ(self._aw, self._conf)
        tz = tzUtil.getDisplayTZ()
        if hasattr(status, 'getResponsible'):
            respPerson = i18nformat(""" _("by") %s""") % self._getAuthorHTML(status.getResponsible()) if status.getResponsible() else ""
        else:
            respPerson = ""

        if status.__class__ == review.AbstractStatusAccepted:
            trackTitle, contribTitle = "", ""
            if status.getTrack():
                trackTitle = " for %s" % self.htmlText(status.getTrack().getTitle())
            if status.getType():
                contribTitle = " as %s" % self.htmlText(status.getType().getName())
            html = i18nformat("""%s%s%s<br><font size="-1">%s _("on") %s</font>""") % (
                html,
                trackTitle,
                contribTitle,
                respPerson,
                getAdjustedDate(status.getDate(), tz=tz).strftime("%d %B %Y %H:%M")
            )
            if status.getComments() != "":
                html = """%s<br><font size="-1"><i>%s</i></font>""" % (
                    html,
                    status.getComments()
                )
        elif status.__class__ == review.AbstractStatusRejected:
            html = i18nformat("""%s<br><font size="-1">%s _("on") %s</font>""") % (
                html,
                respPerson,
                getAdjustedDate(status.getDate(), tz=tz).strftime("%d %B %Y %H:%M")
            )
            if status.getComments() != "":
                html = """%s<br><font size="-1"><i>%s</i></font>""" % (
                    html,
                    status.getComments()
                )
        elif status.__class__ == review.AbstractStatusWithdrawn:
            html = i18nformat("""%s<font size="-1">%s _("on") %s</font>""") % (
                html,
                respPerson,
                getAdjustedDate(status.getDate(), tz=tz).strftime("%d %B %Y %H:%M")
            )
            if status.getComments() != "":
                html = """%s<br><font size="-1"><i>%s</i></font>""" % (
                    html,
                    status.getComments()
                )
        elif status.__class__ == review.AbstractStatusDuplicated:
            original = status.getOriginal()
            url = urlHandlers.UHAbstractManagment.getURL(original)
            html = i18nformat("""%s (<a href=%s>%s-<i>%s</i></a>) <font size="-1">%s _("on") %s</font>""") % (
                html,
                quoteattr(str(url)),
                self.htmlText(original.getId()),
                self.htmlText(original.getTitle()),
                respPerson,
                getAdjustedDate(status.getDate(), tz=tz).strftime("%d %B %Y %H:%M")
            )
            if status.getComments() != "":
                html = """%s<br><font size="-1"><i>%s</i></font>""" % (
                    html,
                    status.getComments()
                )
        elif status.__class__ == review.AbstractStatusMerged:
            target = status.getTargetAbstract()
            url = urlHandlers.UHAbstractManagment.getURL(target)
            html = i18nformat("""<font color="black"><b>%s</b></font> (<a href=%s>%s-<i>%s</i></a>) <font size="-1">%s _("on") %s</font>""") % (
                html,
                quoteattr(str(url)),
                self.htmlText(target.getId()),
                self.htmlText(target.getTitle()),
                respPerson,
                getAdjustedDate(status.getDate(), tz=tz).strftime("%d %B %Y %H:%M")
            )
            if status.getComments() != "":
                html = """%s<br><font size="-1"><i>%s</i></font>""" % (
                    html,
                    status.getComments()
                )
        return html

    def _getTracksHTML(self):
        prog = []
        for track in self._abstract.getTrackListSorted():
            jud = self._abstract.getTrackJudgement(track)
            if jud.__class__ == review.AbstractAcceptance:
                cTypeCaption = ""
                if jud.getContribType() is not None:
                    cTypeCaption = jud.getContribType().getName()
                st = i18nformat(""" - _("Proposed to accept")""")
                if cTypeCaption:
                    st += self.htmlText(cTypeCaption)
                color = """ color="#009933" """
            elif jud.__class__ == review.AbstractRejection:
                st = i18nformat("""- _("Proposed to reject")""")
                color = """ color="red" """
            elif jud.__class__ == review.AbstractReallocation:
                st = i18nformat("""- _("Proposed for other tracks")""")
                color = """ color="black" """
            elif jud.__class__ == review.AbstractInConflict:
                st = i18nformat("""- _("Conflict")""")
                color = """ color="red" """
            else:
                st = ""
                color = ""
            if st != "":
                prog.append("""<li>%s <font size="-1" %s> %s </font></li>""" % (self.htmlText(track.getTitle()), color, st))
            else:
                prog.append("""<li>%s</li>""" % (self.htmlText(track.getTitle())))
        return "<ul>%s</ul>" % "".join(prog)

    def _getContributionHTML(self):
        res = ""
        contrib = self._abstract.getContribution()
        if contrib:
            url = urlHandlers.UHContributionModification.getURL(contrib)
            title = self.htmlText(contrib.getTitle())
            id = self.htmlText(contrib.getId())
            res = """<a href=%s>%s - %s</a>""" % (quoteattr(str(url)), id, title)
        return res

    def _getMergeFromHTML(self):
        abstracts = self._abstract.getMergeFromList()
        if not abstracts:
            return ""
        l = []
        for abstract in abstracts:
            if abstract.getOwner():
                l.append("""<a href="%s">%s : %s</a><br>\n""" % (urlHandlers.UHAbstractManagment.getURL(abstract), abstract.getId(), abstract.getTitle()))
            else:
                l.append("""%s : %s [DELETED]<br>\n""" % (abstract.getId(), abstract.getTitle()))

        return i18nformat("""<tr>
                    <td class="dataCaptionTD" nowrap><span class="dataCaptionFormat"> _("Merged from")</span></td>
                    <td bgcolor="white" valign="top" colspan="3">%s</td>
                </tr>""") % "".join(l)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["abstract"] = self._abstract

        afm = self._abstract.getConference().getAbstractMgr().getAbstractFieldsMgr()
        vars["additionalFields"] = afm.getActiveFields()
        vars["organisation"] = self.htmlText(self._abstract.getSubmitter().getAffiliation())
        vars["status"] = self._getStatusHTML()
        vars["statusName"] = AbstractStatusList.getInstance().getCaption(self._abstract.getCurrentStatus().__class__).upper()
        vars["showBackToSubmitted"] = isinstance(self._abstract.getCurrentStatus(), (review.AbstractStatusWithdrawn,
                                                                                     review.AbstractStatusRejected,
                                                                                     review.AbstractStatusAccepted))
        #for author in self._abstract.getAuthorList():
        #    if self._abstract.isPrimaryAuthor( author ):
        #        primary_authors.append( self._getAuthorHTML( author ) )
        #    else:
        #        co_authors.append( self._getAuthorHTML( author ) )
        primary_authors = []
        for author in self._abstract.getPrimaryAuthorList():
            primary_authors.append(self._getAuthorHTML(author))
        co_authors = []
        for author in self._abstract.getCoAuthorList():
            co_authors.append(self._getAuthorHTML(author))
        vars["primary_authors"] = "<br>".join(primary_authors)
        vars["co_authors"] = "<br>".join(co_authors)
        speakers = []
        for spk in self._abstract.getSpeakerList():
            speakers.append(self._getAuthorHTML(spk))
        vars["speakers"] = "<br>".join(speakers)
        vars["tracks"] = self._getTracksHTML()
        vars["type"] = ""
        if self._abstract.getContribType() is not None:
            vars["type"] = self._abstract.getContribType().getName()
        vars["submitDate"] = self._abstract.getSubmissionDate().strftime("%d %B %Y %H:%M")
        vars["modificationDate"] = self._abstract.getModificationDate().strftime("%d %B %Y %H:%M")
        vars["disable"] = ""
        vars["dupDisable"] = ""
        vars["mergeDisable"] = ""
        if self._abstract.getCurrentStatus().__class__ in [review.AbstractStatusAccepted,
                                                           review.AbstractStatusRejected,
                                                           review.AbstractStatusWithdrawn]:
            vars["disable"] = "disabled"
            vars["mergeDisable"] = "disabled"
            vars["dupDisable"] = "disabled"

        vars["duplicatedButton"] = _("mark as duplicated")
        vars["duplicateURL"] = quoteattr(str(urlHandlers.UHAbstractModMarkAsDup.getURL(self._abstract)))
        if self._abstract.getCurrentStatus().__class__ == review.AbstractStatusDuplicated:
            vars["duplicatedButton"] = _("unmark as duplicated")
            vars["duplicateURL"] = quoteattr(str(urlHandlers.UHAbstractModUnMarkAsDup.getURL(self._abstract)))
            vars["mergeDisable"] = "disabled"
            vars["disable"] = "disabled"

        vars["mergeButton"] = _("merge into")
        vars["mergeIntoURL"] = quoteattr(str(urlHandlers.UHAbstractModMergeInto.getURL(self._abstract)))
        if self._abstract.getCurrentStatus().__class__ == review.AbstractStatusMerged:
            vars["mergeIntoURL"] = quoteattr(str(urlHandlers.UHAbstractModUnMerge.getURL(self._abstract)))
            vars["mergeButton"] = _("unmerge")
            vars["dupDisable"] = "disabled"
            vars["disable"] = "disabled"

        vars["mergeFrom"] = self._getMergeFromHTML()

        vars["abstractListURL"] = quoteattr(str(urlHandlers.UHConfAbstractManagment.getURL(self._conf)))
        vars["viewTrackDetailsURL"] = quoteattr(str(urlHandlers.UHAbstractTrackProposalManagment.getURL(self._abstract)))
        vars["comments"] = self._abstract.getComments()
        vars["contribution"] = self._getContributionHTML()
        vars["abstractPDF"] = urlHandlers.UHAbstractConfManagerDisplayPDF.getURL(self._abstract)
        vars["printIconURL"] = Config.getInstance().getSystemIconURL("pdf")
        vars["abstractXML"] = urlHandlers.UHAbstractToXML.getURL(self._abstract)
        vars["xmlIconURL"] = Config.getInstance().getSystemIconURL("xml")
        vars["acceptURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentAccept.getURL(self._abstract)))
        vars["rejectURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentReject.getURL(self._abstract)))
        vars["changeTrackURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentChangeTrack.getURL(self._abstract)))
        vars["backToSubmittedURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentBackToSubmitted.getURL(self._abstract)))
        vars["modDataURL"] = quoteattr(str(urlHandlers.UHAbstractModEditData.getURL(self._abstract)))
        vars["propToAccURL"] = quoteattr(str(urlHandlers.UHConfModAbstractPropToAcc.getURL(self._abstract)))
        vars["propToRejURL"] = quoteattr(str(urlHandlers.UHConfModAbstractPropToRej.getURL(self._abstract)))
        vars["withdrawURL"] = quoteattr(str(urlHandlers.UHConfModAbstractWithdraw.getURL(self._abstract)))
        vars["disableWithdraw"] = ""
        if self._abstract.getCurrentStatus().__class__ not in \
                [review.AbstractStatusSubmitted, review.AbstractStatusAccepted,
                    review.AbstractStatusInConflict,
                    review.AbstractStatusUnderReview,
                    review.AbstractStatusProposedToReject,
                    review.AbstractStatusProposedToAccept]:
            vars["disableWithdraw"] = " disabled"

        rating = self._abstract.getRating()
        if rating is None:
            vars["rating"] = ""
        else:
            vars["rating"] = "%.2f" % rating
        vars["scaleLower"] = self._abstract.getConference().getConfAbstractReview().getScaleLower()
        vars["scaleHigher"] = self._abstract.getConference().getConfAbstractReview().getScaleHigher()
        vars["attachments"] = fossilize(self._abstract.getAttachments().values(), ILocalFileAbstractMaterialFossil)
        vars["confId"] = self._conf.getId()
        vars["confTitle"] = self._conf.getTitle()
        vars["submitterFullName"] = self._abstract.getSubmitter().getFullName()
        vars["submitterAffiliation"] = self._abstract.getSubmitter().getAffiliation()
        vars["submitterEmail"] = self._abstract.getSubmitter().getEmail()
        vars["abstractAccepted"] = isinstance(self._abstract.getCurrentStatus(), review.AbstractStatusAccepted)

        return vars


class WPAbstractManagment(WPAbstractManagementBase):

    def _setActiveTab( self ):
        self._tabMain.setActive()

    def _getTabContent( self, params ):
        wc = WAbstractManagment( self._getAW(), self._target )
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

    def __init__( self, aw, abstract, track=None ):
        self._abstract = abstract
        self._track = track
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
            #   [C] -> track in conflict
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
                elif isinstance(jud, review.AbstractInConflict):
                    indicator = "[C] "
            items.append("""<option value="%s"%s>%s%s</option>"""%(track.getId(), selected, indicator, track.getTitle()))
        return items

    def _getSessionItemsHTML( self ):
        items = [ i18nformat("""<option value="conf">--_("no session")--</option>""")]
        for session in self._conf.getSessionList():
            items.append("""<option value="%s">%s</option>"""%(session.getId(), session.getTitle()))
        return items

    def _checkNotificationTpl(self):
        for notificationTpl in self._abstract.getOwner().getNotificationTplList():
            for condition in notificationTpl.getConditionList():
                if isinstance(condition, review.NotifTplCondAccepted):
                    return True
        return False

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractName"] = self._abstract.getTitle()
        vars["tracks"] = "".join( self._getTrackItemsHTML() )
        vars["sessions"] = "".join( self._getSessionItemsHTML() )
        vars["types"] = "".join( self._getTypeItemsHTML() )
        vars["showNotifyCheckbox"] = self._checkNotificationTpl()

        if self._track == None:
            vars["acceptURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentAccept.getURL(self._abstract)))
            vars["cancelURL"] = quoteattr(str(urlHandlers.UHAbstractManagment.getURL(self._abstract)))
            vars["trackTitle"] = ""
        else:
            vars["acceptURL"] = quoteattr(str(urlHandlers.UHTrackAbstractAccept.getURL(self._track, self._abstract)))
            vars["cancelURL"] = quoteattr(str(urlHandlers.UHTrackAbstractModif.getURL(self._track, self._abstract)))
            vars["trackTitle"] = self._track.getTitle()
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

    def __init__( self, aw, abstract, track=None ):
        self._abstract = abstract
        self._track = track
        self._aw = aw
        self._conf = abstract.getOwner().getOwner()

    def _checkNotificationTpl(self):
        for notificationTpl in self._abstract.getOwner().getNotificationTplList():
            for condition in notificationTpl.getConditionList():
                if isinstance(condition, review.NotifTplCondRejected):
                    return True
        return False

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["abstractName"] = self._abstract.getTitle()
        vars["showNotifyCheckbox"] = self._checkNotificationTpl()
        if self._track == None:
            vars["rejectURL"] = quoteattr(str(urlHandlers.UHAbstractManagmentReject.getURL(self._abstract)))
            vars["cancelURL"] = quoteattr(str(urlHandlers.UHAbstractManagment.getURL(self._abstract)))
            vars["trackTitle"] = ""
        else:
            vars["rejectURL"] = quoteattr(str(urlHandlers.UHTrackAbstractReject.getURL(self._track, self._abstract)))
            vars["cancelURL"] = quoteattr(str(urlHandlers.UHTrackAbstractModif.getURL(self._track, self._abstract)))
            vars["trackTitle"] = self._track.getTitle()
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

    def _getTabContent(self, params):
        wc = wcomponents.WAbstractModMarkAsDup(self._target)
        p = {"comments": params.get("comments", ""),
             "id": params.get("originalId", ""),
             "duplicateURL": urlHandlers.UHAbstractModMarkAsDup.getURL(self._abstract),
             "cancelURL": urlHandlers.UHAbstractManagment.getURL(self._abstract),
             "error": params.get('errorMsg', '')}
        return wc.getHTML(p)


class WPModUnMarkAsDup(WPAbstractManagment):

    def _getTabContent(self, params):
        wc = wcomponents.WAbstractModUnMarkAsDup(self._target)
        p = {"comments": params.get("comments", ""),
             "unduplicateURL": urlHandlers.UHAbstractModUnMarkAsDup.getURL(self._abstract),
             "cancelURL": urlHandlers.UHAbstractManagment.getURL(self._abstract)}
        return wc.getHTML(p)



class WAbstractModMergeInto(wcomponents.WTemplated):

    def __init__(self,abstract):
        self._abstract=abstract

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["mergeURL"]=quoteattr(str(vars["mergeURL"]))
        vars["cancelURL"]=quoteattr(str(vars["cancelURL"]))
        vars["includeAuthorsChecked"]=""
        if vars.get("includeAuthors",False):
            vars["includeAuthorsChecked"]=" checked"
        vars["notifyChecked"]=""
        if vars.get("doNotify",False):
            vars["notifyChecked"]=" checked"
        return vars


class WPModMergeInto(WPAbstractManagment):

    def _getTabContent(self, params):
        wc = WAbstractModMergeInto(self._target)
        p = {"cancelURL": urlHandlers.UHAbstractManagment.getURL(self._abstract),
             "mergeURL": urlHandlers.UHAbstractModMergeInto.getURL(self._abstract),
             "comments": params.get("comments", ""),
             "id": params.get("targetId", ""),
             "includeAuthors": params.get("includeAuthors", False),
             "doNotify": params.get("notify", False),
             "error": params.get('errorMsg', '')}
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

    def _getTabContent(self, params):
        wc = WAbstractModUnMerge(self._target)
        p = {"comments": params.get("comments", ""),
             "unmergeURL": urlHandlers.UHAbstractModUnMerge.getURL(self._abstract),
             "cancelURL": urlHandlers.UHAbstractManagment.getURL(self._abstract),
             "error": params.get('errorMsg', '')}
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
            elif isinstance(jud,review.AbstractInConflict):
                legend="[C]"
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
            elif isinstance(jud,review.AbstractInConflict):
                legend="[C]"
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

    def _setActiveTab(self):
        self._tabTracks.setActive()
        self._subTabRating.setActive()

    def _getTabContent(self, params):
        wc = WAbstractTrackOrderByRating(self._getAW(), self._target)
        return wc.getHTML(params)


class WPModIntComments(WPAbstractManagementBase):

    def _setActiveTab(self):
        self._tabComments.setActive()

    def _getTabContent(self, params):
        wc = wcomponents.WAbstractModIntComments(self._getAW(), self._target)
        p = {"newCommentURL": urlHandlers.UHAbstractModNewIntComment.getURL(self._abstract),
            "commentEditURLGen": urlHandlers.UHAbstractModIntCommentEdit.getURL,
            "commentRemURLGen": urlHandlers.UHAbstractModIntCommentRem.getURL
        }
        return wc.getHTML(p)


class WPModNewIntComment(WPModIntComments):

    def _getTabContent(self, params):
        wc = wcomponents.WAbstractModNewIntComment(self._getAW(), self._target)
        p = {"postURL": urlHandlers.UHAbstractModNewIntComment.getURL(self._abstract)}
        return wc.getHTML(p)


class WPModIntCommentEdit(WPModIntComments):

    def __init__(self, rh, comment):
        self._comment = comment
        WPModIntComments.__init__(self, rh, comment.getAbstract())

    def _getTabContent(self, params):
        wc = wcomponents.WAbstractModIntCommentEdit(self._comment)
        p = {"postURL": urlHandlers.UHAbstractModIntCommentEdit.getURL(self._comment)}
        return wc.getHTML(p)


class WAbstractModNotifLog(wcomponents.WTemplated):

    def __init__(self, abstract):
        self._abstract = abstract

    def _getResponsibleHTML(self, res):
        conf = self._abstract.getConference()
        tmp = "%s (%s)" % (res.getFullName(), res.getAffiliation())
        tmp = self.htmlText(tmp)

        if res.getEmail() != "":
            mailtoSubject = _("[%s] Abstract %s: %s") % (conf.getTitle(), self._abstract.getId(), self._abstract.getTitle())
            mailtoURL = "mailto:%s?subject=%s" % (res.getEmail(), \
                                            urllib.quote(mailtoSubject))
            href = quoteattr(mailtoURL)
            tmp = """<a href=%s>%s</a>""" % (href, tmp)

        return tmp

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        res = []

        for entry in self._abstract.getNotificationLog().getEntryList():
            d = entry.getDate().strftime("%Y-%m-%d %H:%M")
            resp = entry.getResponsible()
            tplCaption = entry.getTpl().getName()
            tplLink = i18nformat("""
                    <b>%s</b> <font color="red"> _("(This template doesn't exist anymore)")</font>
                    """) % tplCaption

            if entry.getTpl().getOwner() is not None:
                url = urlHandlers.UHAbstractModNotifTplDisplay.getURL(entry.getTpl())
                tplLink = "<a href=%s>%s</a>" % (quoteattr(str(url)), self.htmlText(tplCaption))

            res.append(i18nformat("""
                        <tr>
                            <td bgcolor="white">
                                %s _("by") %s
                                <br>
                                _("notification template used"): %s
                            </td>
                        </tr>
                        """) % (self.htmlText(d), self._getResponsibleHTML(resp), tplLink))

        vars["entries"] = "".join(res)
        return vars


class WPModNotifLog(WPAbstractManagementBase):

    def _setActiveTab(self):
        self._tabNotifLog.setActive()

    def _getTabContent(self, params):
        wc = WAbstractModNotifLog(self._target)
        return wc.getHTML()


class WConfModAbstractWithdraw(wcomponents.WTemplated):

    def __init__(self, aw, abstract):
        self._abstract = abstract
        self._aw = aw

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"] = quoteattr(str(urlHandlers.UHConfModAbstractWithdraw.getURL(self._abstract)))
        vars["comment"] = ""
        return vars


class WPModWithdraw(WPAbstractManagment):

    def _getTabContent(self, params):
        wc = WConfModAbstractWithdraw(self._rh.getAW(), self._abstract)
        return wc.getHTML()


class WAbstractModifTool(wcomponents.WTemplated):

    def __init__(self, contrib):
        self._contrib = contrib

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["deleteIconURL"] = Config.getInstance().getSystemIconURL("delete")
        return vars


class WPModTools(WPAbstractManagment):

    def _setActiveTab(self):
        self._tabTools.setActive()

    def _getTabContent(self, params):
        wc = WAbstractModifTool(self._target)
        pars = { \
            "deleteContributionURL": urlHandlers.UHAbstractDelete.getURL(self._target)
                }
        return wc.getHTML(pars)


class WPModRemConfirmation(WPModTools):

    def __init__(self, rh, abs):
        WPAbstractManagment.__init__(self, rh, abs)
        self._abs = abs

    def _getTabContent(self, params):
        wc = wcomponents.WConfirmation()
        msg = {'challenge': _("Are you sure you want to delete the abstract?"),
               'target': self._abs.getTitle(),
               'subtext': None
               }
        url = urlHandlers.UHAbstractDelete.getURL(self._abs)
        return wc.getHTML(msg, url, {},
                          severity="danger")
