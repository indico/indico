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
import urllib
from xml.sax.saxutils import quoteattr
from datetime import datetime
from pytz import timezone

import MaKaC.conference as conference
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.navigation as navigation
import MaKaC.webinterface.materialFactories as materialFactories
from MaKaC.webinterface.pages.metadata import WICalExportBase
from MaKaC.webinterface.pages.conferences import WPConferenceBase, WPConferenceModifBase, WPConferenceDefaultDisplayBase
from MaKaC.webinterface.pages.main import WPMainBase
from indico.core.config import Config
from MaKaC.common.utils import isStringHTML, formatDateTime
from MaKaC.common import info
from MaKaC.i18n import _
from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.common.fossilize import fossilize
from MaKaC.user import Avatar, AvatarHolder
from MaKaC.fossils.conference import ILocalFileAbstractMaterialFossil

from indico.util.i18n import i18nformat
from indico.util.date_time import format_time, format_date

from indico.util.string import render_markdown
from MaKaC.common.TemplateExec import render


class WPContributionBase(WPMainBase, WPConferenceBase):

    def __init__(self, rh, contribution, hideFull=0):
        self._contrib = self._target = contribution
        WPConferenceBase.__init__(self, rh, self._contrib.getConference())
        self._navigationTarget = contribution
        self._hideFull = hideFull


class WPContributionDefaultDisplayBase(WPConferenceDefaultDisplayBase, WPContributionBase):

    def getJSFiles(self):
        return WPConferenceDefaultDisplayBase.getJSFiles(self) + \
            self._includeJSPackage('Management') + \
            self._includeJSPackage('MaterialEditor') + \
            self._asset_env['contributions_js'].urls()

    def getCSSFiles(self):
        return WPConferenceDefaultDisplayBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def _getHeadContent(self):
        return WPConferenceDefaultDisplayBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])

    def __init__(self, rh, contribution, hideFull=0):
        WPContributionBase.__init__(self, rh, contribution, hideFull)


class WContributionDisplayBase(WICalExportBase):

    def __init__(self, aw, contrib, hideFull=0):
        self._aw = aw
        self._contrib = contrib
        self._hideFull = hideFull

    def _getAuthorURL(self, author):
        return urlHandlers.UHContribAuthorDisplay.getURL(self._contrib, authorId=author.getId())

    def _getResourceName(self, resource):
        if isinstance(resource, conference.Link):
            return resource.getName() if resource.getName() != "" and resource.getName() != resource.getURL() else resource.getURL()
        else:
            return resource.getName() if resource.getName() != "" and resource.getName() != resource.getFileName() else resource.getFileName()

    def _getStatusReviewing(self):
        from MaKaC.paperReviewing import ConferencePaperReview as CPR
        versioning = self._contrib.getReviewManager().getVersioning()
        review = self._contrib.getReviewManager().getLastReview()
        if self._contrib.getConference().getConfPaperReview().getChoice() == CPR.LAYOUT_REVIEWING:
            if review.getEditorJudgement().isSubmitted():  # editor has accepted or rejected
                return review.getEditorJudgement().getJudgement()
            elif review.isAuthorSubmitted():
                return "Submitted"
            elif len(versioning) > 1:  # there was a judgement 'To be corrected' or custom status
                return versioning[-2].getEditorJudgement().getJudgement()
        elif self._contrib.getConference().getConfPaperReview().getChoice() in [CPR.CONTENT_REVIEWING, CPR.CONTENT_AND_LAYOUT_REVIEWING]:
            if review.getRefereeJudgement().isSubmitted():  # referee has accepted or rejected
                return review.getRefereeJudgement().getJudgement()
            elif review.isAuthorSubmitted():
                return "Submitted"
            elif len(versioning) > 1:  # there was a judgement 'To be corrected' or custom status
                return versioning[-2].getRefereeJudgement().getJudgement()
        if review.isAuthorSubmitted():
            return "Submitted"
        return None

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)

        vars["isWithdrawn"] = isinstance(self._contrib.getCurrentStatus(), conference.ContribStatusWithdrawn)
        vars["Contribution"] = vars["target"] = self._contrib
        vars["urlICSFile"] = urlHandlers.UHContribToiCal.getURL(self._contrib)

        vars["showAttachedFiles"] = self._contrib.getConference().getAbstractMgr().showAttachedFilesContribList() and isinstance(self._contrib, conference.AcceptedContribution) and self._contrib.getAbstract() and len(self._contrib.getAbstract().getAttachments()) > 0
        vars["abstractAttachments"] = fossilize(self._contrib.getAbstract().getAttachments().values(), ILocalFileAbstractMaterialFossil) if isinstance(self._contrib, conference.AcceptedContribution) and self._contrib.getAbstract() else []

        vars.update(self._getIcalExportParams(self._aw.getUser(), '/export/event/%s/contribution/%s.ics' %
                                              (self._contrib.getConference().getId(), self._contrib.getId())))

        vars["getAuthorURL"] = lambda auth: self._getAuthorURL(auth)
        vars["formatDate"] = lambda date: format_date(date, "d MMM yyyy")
        vars["formatTime"] = lambda time: format_time(time, format="short", timezone=timezone(DisplayTZ(self._aw, self._contrib.getConference()).getDisplayTZ()))
        vars["accessWrapper"] = self._aw
        statusReviewing = self._getStatusReviewing()
        vars["showSubmit"] = statusReviewing not in ["Accept", "Reject", "Submitted"]
        vars["showMaterial"] = statusReviewing is not None
        vars["showHistory"] = statusReviewing is not None
        vars["reviewingActive"] = self._contrib.getConference() and \
            self._contrib.getConference().getConfPaperReview().hasReviewing() and \
            not isinstance(self._contrib.getCurrentStatus(), conference.ContribStatusWithdrawn) and \
            (self._contrib.canUserSubmit(self._aw.getUser()) or self._contrib.canModify(self._aw))
        if statusReviewing == "Submitted":
            vars["statusText"] = _("Awaiting review")
            vars["statusClass"] = "contributionReviewingStatusPending"
        elif statusReviewing == "Accept":
            vars["statusText"] = _("ACCEPTED")
            vars["statusClass"] = "contributionReviewingStatusAccepted"
        elif statusReviewing == "Reject":
            vars["statusText"] = _("REJECTED")
            vars["statusClass"] = "contributionReviewingStatusRejected"
        elif statusReviewing == "To be corrected":
            vars["statusText"] = _("To be corrected")
            vars["statusClass"] = "contributionReviewingStatusCorrected"
        elif statusReviewing is not None:
            vars["statusText"] = statusReviewing
            vars["statusClass"] = "contributionReviewingStatusCorrected"
        else:
            vars["statusText"] = _("Paper not yet submitted")
            vars["statusClass"] = "contributionReviewingStatusNotSubmitted"
        vars["prefixUpload"] = "Re-" if statusReviewing not in ["Accept", "Reject", None] else ""
        vars["getResourceName"] = lambda resource: self._getResourceName(resource)
        vars["reportNumberSystems"] = Config.getInstance().getReportNumberSystems()
        return vars


class WContributionDisplayFull(WContributionDisplayBase):
    pass


class WContributionDisplayMin(WContributionDisplayBase):
    pass


class WContributionDisplay:

    def __init__(self, aw, contrib, hideFull=0):
        self._aw = aw
        self._contrib = contrib
        self._hideFull = hideFull

    def getHTML(self, params={}):
        if self._contrib.canAccess(self._aw):
            c = WContributionDisplayFull(self._aw, self._contrib, self._hideFull)
            return c.getHTML(params)
        if self._contrib.canView(self._aw):
            c = WContributionDisplayMin(self._aw, self._contrib)
            return c.getHTML(params)
        return ""


class WPContributionDisplay(WPContributionDefaultDisplayBase):
    navigationEntry = navigation.NEContributionDisplay

    def _getBody(self, params):
        wc = WContributionDisplay(self._getAW(), self._contrib, self._hideFull)
        return wc.getHTML()


class WPContributionModifBase(WPConferenceModifBase):

    def __init__(self, rh, contribution):
        WPConferenceModifBase.__init__(self, rh, contribution.getConference())
        self._contrib = self._target = contribution
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager
        self._isPRM = RCPaperReviewManager.hasRights(rh)
        self._canModify = self._contrib.canModify(rh.getAW()) or (self._contrib.getSession() and self._contrib.getSession().canCoordinate(rh.getAW(), "modifContribs"))

    def _getEnabledControls(self):
        return False

    def _getNavigationDrawer(self):
        pars = {"target": self._contrib, "isModif": True}
        return wcomponents.WNavigationDrawer(pars, bgColor="white")

    def _createTabCtrl(self):

        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab("main", _("Main"),
                                             urlHandlers.UHContributionModification.getURL(self._target))
        self._tabMaterials = self._tabCtrl.newTab("materials", _("Material"),
                                                  urlHandlers.UHContribModifMaterials.getURL(self._target))
        self._tabSubCont = self._tabCtrl.newTab("subCont", _("Sub Contribution"),
                                                urlHandlers.UHContribModifSubCont.getURL(self._target))
        if self._canModify:
            self._tabAC = self._tabCtrl.newTab("ac", _("Protection"),
                                               urlHandlers.UHContribModifAC.getURL(self._target))
            self._tabTools = self._tabCtrl.newTab("tools", _("Tools"),
                                                  urlHandlers.UHContribModifTools.getURL(self._target))

        hasReviewingEnabled = self._contrib.getConference().hasEnabledSection('paperReviewing')
        paperReviewChoice = self._contrib.getConference().getConfPaperReview().getChoice()

        if hasReviewingEnabled and paperReviewChoice != 1:
            if self._canModify or self._isPRM or self._contrib.getReviewManager().isReferee(self._rh._getUser()):
                self._subtabReviewing = self._tabCtrl.newTab("reviewing", "Paper Reviewing",
                                                             urlHandlers.UHContributionModifReviewing.getURL(self._target))
            else:
                if self._contrib.getReviewManager().isEditor(self._rh._getUser()):
                    self._subtabReviewing = self._tabCtrl.newTab("reviewing", "Paper Reviewing",
                                                                 urlHandlers.UHContributionEditingJudgement.getURL(self._target))
                elif self._contrib.getReviewManager().isReviewer(self._rh._getUser()):
                    self._subtabReviewing = self._tabCtrl.newTab("reviewing", "Paper Reviewing",
                                                                 urlHandlers.UHContributionGiveAdvice.getURL(self._target))

            if self._canModify or self._isPRM or self._contrib.getReviewManager().isReferee(self._rh._getUser()):
                self._subTabAssign = self._subtabReviewing.newSubTab("assign", _("Assign Team"),
                                                                     urlHandlers.UHContributionModifReviewing.getURL(self._target))
                if self._contrib.getReviewManager().isReferee(self._rh._getUser()) and not (paperReviewChoice == 3 or paperReviewChoice == 1):
                    self._subTabJudgements = self._subtabReviewing.newSubTab("referee", _("Referee Assessment"),
                                                                             urlHandlers.UHContributionReviewingJudgements.getURL(self._target))
                else:
                    self._subTabJudgements = self._subtabReviewing.newSubTab("Assessments", _("Assessments"),
                                                                             urlHandlers.UHContributionReviewingJudgements.getURL(self._target))

            if (paperReviewChoice == 3 or paperReviewChoice == 4) and \
               self._contrib.getReviewManager().isEditor(self._rh._getUser()) and \
               not self._contrib.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted():
                self._tabJudgeEditing = self._subtabReviewing.newSubTab("editing", "Assess Layout",
                                                                        urlHandlers.UHContributionEditingJudgement.getURL(self._target))

            if (paperReviewChoice == 2 or paperReviewChoice == 4) and \
               self._contrib.getReviewManager().isReviewer(self._rh._getUser()) and \
               not self._contrib.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted():
                self._tabGiveAdvice = self._subtabReviewing.newSubTab("advice", "Assess Content",
                                                                      urlHandlers.UHContributionGiveAdvice.getURL(self._target))

            if self._canModify or \
               self._isPRM or \
               self._contrib.getReviewManager().isInReviewingTeamforContribution(self._rh._getUser()):
                self._subTabRevMaterial = self._subtabReviewing.newSubTab("revmaterial", _("Material to Review"),
                                                                          urlHandlers.UHContribModifReviewingMaterials.getURL(self._target))

            if self._canModify or \
               self._isPRM or \
               self._contrib.getReviewManager().isReferee(self._rh._getUser()) or \
               len(self._contrib.getReviewManager().getVersioning()) > 1 or \
               self._contrib.getReviewManager().getLastReview().getRefereeJudgement().isSubmitted():
                self._subTabReviewingHistory = self._subtabReviewing.newSubTab("reviewing_history", "History",
                                                                               urlHandlers.UHContributionModifReviewingHistory.getURL(self._target))

        self._setActiveTab()
        self._setupTabCtrl()

    def _setActiveTab(self):
        pass

    def _setupTabCtrl(self):
        pass

    def _setActiveSideMenuItem(self):
        if self._target.isScheduled():
            self._timetableMenuItem.setActive(True)
        else:
            self._contribListMenuItem.setActive(True)

    def _getPageContent(self, params):
        self._createTabCtrl()
        banner = ""
        if self._canModify or self._isPRM:
            banner = wcomponents.WTimetableBannerModif(self._getAW(), self._target).getHTML()
        else:
            if self._conf.getConfPaperReview().isRefereeContribution(self._rh._getUser(), self._contrib):
                banner = wcomponents.WListOfPapersToReview(self._target, "referee").getHTML()
            if self._conf.getConfPaperReview().isReviewerContribution(self._rh._getUser(), self._contrib):
                banner = wcomponents.WListOfPapersToReview(self._target, "reviewer").getHTML()
            if self._conf.getConfPaperReview().isEditorContribution(self._rh._getUser(), self._contrib):
                banner = wcomponents.WListOfPapersToReview(self._target, "editor").getHTML()
        if banner == "":
            banner = wcomponents.WTimetableBannerModif(self._getAW(), self._target).getHTML()

        body = wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))
        return banner + body

    def _getHeadContent(self):
        return WPConferenceModifBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
            self._asset_env['abstracts_js'].urls()


class WPContribModifMain(WPContributionModifBase):

    def _setActiveTab(self):
        self._tabMain.setActive()


class WPContributionModifTools(WPContributionModifBase):

    def _setActiveTab(self):
        self._tabTools.setActive()

    def _getTabContent(self, params):
        return wcomponents.WContribModifTool().getHTML({"deleteContributionURL": urlHandlers.UHContributionDelete.getURL(self._target)})


class WPContributionModifMaterials(WPContributionModifBase):

    _userData = ['favorite-user-list']

    def __init__(self, rh, contribution):
        WPContributionModifBase.__init__(self, rh, contribution)

    def _setActiveTab(self):
        self._tabMaterials.setActive()

    def _getTabContent(self, pars):
        wc = wcomponents.WShowExistingMaterial(self._target, mode='management', showTitle=True)
        return wc.getHTML(pars)


class WAuthorTable(wcomponents.WTemplated):

    def __init__(self, authList, contrib):
        self._list = authList
        self._conf = contrib.getConference()
        self._contrib = contrib

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        urlGen = vars.get("modAuthorURLGen", None)
        l = []
        for author in self._list:
            authCaption = author.getFullName()
            if author.getAffiliation() != "":
                authCaption = "%s (%s)" % (authCaption, author.getAffiliation())
            if urlGen:
                authCaption = """<a href=%s>%s</a>""" % (urlGen(author), self.htmlText(authCaption))
            href = "\"\""
            if author.getEmail() != "":
                mailtoSubject = """[%s] _("Contribution") %s: %s""" % (self._conf.getTitle(), self._contrib.getId(), self._contrib.getTitle())
                mailtoURL = "mailto:%s?subject=%s" % (author.getEmail(), urllib.quote(mailtoSubject))
                href = quoteattr(mailtoURL)
            emailHtml = """ <a href=%s><img src="%s" style="border:0px" alt="email"></a> """ % (href, Config.getInstance().getSystemIconURL("smallEmail"))
            upURLGen = vars.get("upAuthorURLGen", None)
            up = ""
            if upURLGen is not None:
                up = """<a href=%s><img src=%s border="0" alt="up"></a>""" % (quoteattr(str(upURLGen(author))), quoteattr(str(Config.getInstance().getSystemIconURL("upArrow"))))
            downURLGen = vars.get("downAuthorURLGen", None)
            down = ""
            if downURLGen is not None:
                down = """<a href=%s><img src=%s border="0" alt="down"></a>""" % (quoteattr(str(downURLGen(author))), quoteattr(str(Config.getInstance().getSystemIconURL("downArrow"))))
            l.append("""<input type="checkbox" name="selAuthor" value=%s>%s%s%s %s""" % (quoteattr(author.getId()), up, down, emailHtml, authCaption))
        vars["authors"] = "<br>".join(l)
        vars["remAuthorsURL"] = vars.get("remAuthorsURL", "")
        vars["addAuthorsURL"] = vars.get("addAuthorsURL", "")
        vars["searchAuthorURL"] = vars.get("searchAuthorURL", "")
        return vars


class WContribModifMain(wcomponents.WTemplated):

    def __init__(self, contribution, mfRegistry, eventType="conference"):
        self._contrib = contribution
        self._mfRegistry = mfRegistry
        self._eventType = eventType

    def _getAbstractHTML(self):
        if not self._contrib.getConference().getAbstractMgr().isActive() or not self._contrib.getConference().hasEnabledSection("cfa"):
            return ""
        abs = self._contrib.getAbstract()
        if abs is not None:
            html = i18nformat("""
             <tr>
                <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Abstract")</span></td>
                <td bgcolor="white" class="blacktext"><a href=%s>%s - %s</a></td>
            </tr>
            <tr>
                <td colspan="3" class="horizontalLine">&nbsp;</td>
            </tr>
                """) % (quoteattr(str(urlHandlers.UHAbstractManagment.getURL(abs))),
                        self.htmlText(abs.getId()), abs.getTitle())
        else:
            html = i18nformat("""
             <tr>
                <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Abstract")</span></td>
                <td bgcolor="white" class="blacktext">&nbsp;&nbsp;&nbsp;<font color="red"> _("The abstract associated with this contribution has been removed")</font></td>
            </tr>
            <tr>
                <td colspan="3" class="horizontalLine">&nbsp;</td>
            </tr>
                """)
        return html

    def _getChangeTracksHTML(self):
        res = []
        if not self._contrib.getTrack() is None:
            res = [i18nformat("""<option value="">--_("none")--</option>""")]
        for track in self._contrib.getConference().getTrackList():
            if self._contrib.getTrack() == track:
                continue
            res.append("""<option value=%s>%s</option>""" % (quoteattr(str(track.getId())), self.htmlText(track.getTitle())))
        return "".join(res)

    def _getChangeSessionsHTML(self):
        res = []
        if not self._contrib.getSession() is None:
            res = [i18nformat("""<option value="">--_("none")--</option>""")]
        for session in self._contrib.getConference().getSessionListSorted():
            if self._contrib.getSession() == session or session.isClosed():
                continue
            from MaKaC.common.TemplateExec import truncateTitle
            res.append("""<option value=%s>%s</option>""" % (quoteattr(str(session.getId())), self.htmlText(truncateTitle(session.getTitle(), 60))))
        return "".join(res)

    def _getWithdrawnNoticeHTML(self):
        res = ""
        status = self._contrib.getCurrentStatus()
        if isinstance(status, conference.ContribStatusWithdrawn):
            res = i18nformat("""
                <tr>
                    <td align="center"><b>--_("WITHDRAWN")--</b></td>
                </tr>
                """)
        return res

    def _getWithdrawnInfoHTML(self):
        status = self._contrib.getCurrentStatus()
        if not isinstance(status, conference.ContribStatusWithdrawn):
            return ""
        comment = ""
        if status.getComment() != "":
            comment = """<br><i>%s""" % self.htmlText(status.getComment())
        d = self.htmlText(status.getDate().strftime("%Y-%b-%D %H:%M"))
        resp = ""
        if status.getResponsible() is not None:
            resp = "by %s" % self.htmlText(status.getResponsible().getFullName())
        html = i18nformat("""
     <tr>
        <td class="dataCaptionTD"><span class="dataCaptionFormat"> _("Withdrawal information")</span></td>
        <td bgcolor="white" class="blacktext"><b> _("WITHDRAWN")</b> _("on") %s %s%s</td>
    </tr>
    <tr>
        <td colspan="3" class="horizontalLine">&nbsp;</td>
    </tr>
            """) % (d, resp, comment)
        return html

    def _getParticipantsList(self, participantList):
        result = []
        for part in participantList:
            partFossil = fossilize(part)
            # var to control if we have to show the entry in the author menu to allow add submission rights
            isSubmitter = False
            av = AvatarHolder().match({"email": part.getEmail()}, searchInAuthenticators=False, exact=True)
            if not av:
                if part.getEmail().lower() in self._contrib.getSubmitterEmailList():
                    isSubmitter = True
            elif (av[0] in self._contrib.getSubmitterList() or self._contrib.getConference().getPendingQueuesMgr().isPendingSubmitter(part)):
                isSubmitter = True
            partFossil["showSubmitterCB"] = not isSubmitter
            result.append(partFossil)
        return result

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["eventType"] = self._eventType
        vars["withdrawnNotice"] = self._getWithdrawnNoticeHTML()
        vars["locator"] = self._contrib.getLocator().getWebForm()
        vars["title"] = self._contrib.getTitle()
        if isStringHTML(self._contrib.getDescription()):
            vars["description"] = self._contrib.getDescription()
        else:
            vars["description"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._contrib.getDescription()

        afm = self._contrib.getConference().getAbstractMgr().getAbstractFieldsMgr()
        vars["additionalFields"] = afm.getActiveFields()

        vars["rowspan"] = "6"
        vars["place"] = ""
        if self._contrib.getLocation():
            vars["place"] = self.htmlText(self._contrib.getLocation().getName())
        room = self._contrib.getRoom()
        if room is not None and room.getName().strip() != "":
            vars["place"] = i18nformat("""%s <br> _("Room"): %s""") % (vars["place"], self.htmlText(room.getName()))
        if self._eventType == "conference" and self._contrib.getBoardNumber() != "" and self._contrib.getBoardNumber() is not None:
            vars["place"] = i18nformat("""%s<br> _("Board #")%s""") % (vars["place"], self.htmlText(self._contrib.getBoardNumber()))
        vars["id"] = self.htmlText(self._contrib.getId())
        vars["dataModificationURL"] = str(urlHandlers.UHContributionDataModification.getURL(self._contrib))
        vars["duration"] = ""
        if self._contrib.getDuration() is not None:
            vars["duration"] = (datetime(1900, 1, 1) + self._contrib.getDuration()).strftime("%Hh%M'")
        vars["type"] = ""
        if self._contrib.getType():
            vars["type"] = self.htmlText(self._contrib.getType().getName())
        vars["track"] = i18nformat("""--_("none")--""")
        if self._contrib.getTrack():
            vars["track"] = """<a href=%s>%s</a>""" % (quoteattr(str(urlHandlers.UHTrackModification.getURL(self._contrib.getTrack()))), self.htmlText(self._contrib.getTrack().getTitle()))
        vars["session"] = ""
        if self._contrib.getSession():
            vars["session"] = """<a href=%s>%s</a>""" % (quoteattr(str(urlHandlers.UHSessionModification.getURL(self._contrib.getSession()))), self.htmlText(self._contrib.getSession().getTitle()))
        vars["abstract"] = ""
        if isinstance(self._contrib, conference.AcceptedContribution):
            vars["abstract"] = self._getAbstractHTML()
        vars["contrib"] = self._contrib
        vars["selTracks"] = self._getChangeTracksHTML()
        vars["setTrackURL"] = quoteattr(str(urlHandlers.UHContribModSetTrack.getURL(self._contrib)))
        vars["selSessions"] = self._getChangeSessionsHTML()
        vars["setSessionURL"] = quoteattr(str(urlHandlers.UHContribModSetSession.getURL(self._contrib)))
        vars["contribXML"] = urlHandlers.UHContribToXMLConfManager.getURL(self._contrib)
        vars["contribPDF"] = urlHandlers.UHContribToPDFConfManager.getURL(self._contrib)
        vars["printIconURL"] = Config.getInstance().getSystemIconURL("pdf")
        vars["xmlIconURL"] = Config.getInstance().getSystemIconURL("xml")
        vars["withdrawURL"] = quoteattr(str(urlHandlers.UHContribModWithdraw.getURL(self._contrib)))
        vars["withdrawnInfo"] = self._getWithdrawnInfoHTML()
        vars["withdrawDisabled"] = False
        if isinstance(self._contrib.getCurrentStatus(), conference.ContribStatusWithdrawn):
            vars["withdrawDisabled"] = True
        vars["reportNumbersTable"] = wcomponents.WReportNumbersTable(self._contrib, "contribution").getHTML()
        vars["keywords"] = self._contrib.getKeywords()
        if self._contrib.getSession():
            vars["sessionType"] = self._contrib.getSession().getScheduleType()
        else:
            vars["sessionType"] = 'none'
        vars["primaryAuthors"] = self._getParticipantsList(self._contrib.getPrimaryAuthorList())
        vars["coAuthors"] = self._getParticipantsList(self._contrib.getCoAuthorList())
        vars["speakers"] = self._getParticipantsList(self._contrib.getSpeakerList())
        return vars


class WPContributionModification(WPContribModifMain):

    def _getTabContent(self, params):
        wc = WContribModifMain(self._contrib, materialFactories.ContribMFRegistry())
        return wc.getHTML()


class WPContributionModificationClosed(WPContribModifMain):

    def _createTabCtrl(self):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab("main", _("Main"), "")

    def _getTabContent(self, params):
        if self._contrib.getSession() is not None:
            message = _("The session is currently locked and you cannot modify it in this status. ")
            if self._contrib.getConference().canModify(self._rh.getAW()):
                message += _("If you unlock the session, you will be able to modify its details again.")
            url = urlHandlers.UHSessionOpen.getURL(self._contrib.getSession())
            unlockButtonCaption = _("Unlock session")
        else:
            message = _("The event is currently locked and you cannot modify it in this status. ")
            if self._conf.canModify(self._rh.getAW()):
                message += _("If you unlock the event, you will be able to modify its details again.")
            url = urlHandlers.UHConferenceOpen.getURL(self._contrib.getConference())
            unlockButtonCaption = _("Unlock event")
        return wcomponents.WClosed().getHTML({"message": message,
                                             "postURL": url,
                                             "showUnlockButton": self._contrib.getConference().canModify(self._rh.getAW()),
                                             "unlockButtonCaption": unlockButtonCaption})


class WContribModWithdraw(wcomponents.WTemplated):

    def __init__(self, contrib):
        self._contrib = contrib

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["postURL"] = quoteattr(str(urlHandlers.UHContribModWithdraw.getURL(self._contrib)))
        vars["comment"] = self.htmlText("")
        return vars


class WPModWithdraw(WPContribModifMain):

    def _getTabContent(self, params):
        wc = WContribModWithdraw(self._target)
        return wc.getHTML()


class WContribModifAC(wcomponents.WTemplated):

    def __init__(self, contrib):
        self._contrib = contrib

    def _getManagersList(self):
        result = fossilize(self._contrib.getManagerList())
        # get pending users
        for email in self._contrib.getAccessController().getModificationEmail():
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result

    def _getSubmittersList(self):
        result = []
        for submitter in self._contrib.getSubmitterList():
            submitterFossil = fossilize(submitter)
            if isinstance(submitter, Avatar):
                isSpeaker = False
                if self._contrib.getConference().getType() == "conference":
                    isPrAuthor = False
                    isCoAuthor = False
                    if self._contrib.isPrimaryAuthorByEmail(submitter.getEmail()):
                        isPrAuthor = True
                    if self._contrib.isCoAuthorByEmail(submitter.getEmail()):
                        isCoAuthor = True
                    submitterFossil["isPrAuthor"] = isPrAuthor
                    submitterFossil["isCoAuthor"] = isCoAuthor
                if self._contrib.isSpeakerByEmail(submitter.getEmail()):
                    isSpeaker = True
                submitterFossil["isSpeaker"] = isSpeaker
            result.append(submitterFossil)
        # get pending users
        for email in self._contrib.getSubmitterEmailList():
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        mcf = wcomponents.WModificationControlFrame()
        vars["modifyControlFrame"] = mcf.getHTML(self._contrib)
        acf = wcomponents.WAccessControlFrame()
        visURL = urlHandlers.UHContributionSetVisibility.getURL(self._contrib)

        if isinstance(self._contrib.getOwner(), conference.Session):
            vars["accessControlFrame"] = acf.getHTML(self._contrib, visURL, "InSessionContribution")
        else:
            vars["accessControlFrame"] = acf.getHTML(self._contrib, visURL, "Contribution")

        if not self._contrib.isProtected():
            df = wcomponents.WDomainControlFrame(self._contrib)
            vars["accessControlFrame"] += "<br>%s" % df.getHTML()
        vars["confId"] = self._contrib.getConference().getId()
        vars["contribId"] = self._contrib.getId()
        vars["eventType"] = self._contrib.getConference().getType()
        vars["managers"] = self._getManagersList()
        vars["submitters"] = self._getSubmittersList()
        return vars


class WPContribModifAC(WPContributionModifBase):

    def _setActiveTab(self):
        self._tabAC.setActive()

    def _getTabContent(self, params):
        wc = WContribModifAC(self._target)
        return wc.getHTML()


class WPContribModifSC(WPContributionModifBase):

    def _setActiveTab(self):
        self._tabSubCont.setActive()

    def _getTabContent(self, params):
        wc = wcomponents.WContribModifSC(self._target)
        pars = {
            'moveSubContribURL': urlHandlers.UHSubContribActions.getURL(self._contrib),
            'addSubContURL': urlHandlers.UHContribAddSubCont.getURL(self._contrib),
            'subContModifURL': urlHandlers.UHSubContribModification.getURL  # the () are NOT missing
        }
        return wc.getHTML(pars)

#-----------------------------------------------------------------------------


class WSubContributionCreation(wcomponents.WTemplated):

    def __init__(self, target):
        self.__owner = target
        self._contribution = target

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["title"] = vars.get("title", "")
        vars["description"] = vars.get("description", "")
        vars["durationHours"] = vars.get("durationHours", "0")
        vars["durationMinutes"] = vars.get("durationMinutes", "15")
        vars["keywords"] = vars.get("keywords", "")
        vars["locator"] = self.__owner.getLocator().getWebForm()
        vars["authors"] = fossilize(self._contribution.getAllAuthors())
        vars["eventType"] = self._contribution.getConference().getType()
        return vars


class WPContribAddSC(WPContributionModifBase):

    def _setActiveTab(self):
        self._tabSubCont.setActive()

    def _getTabContent(self, params):
        wc = WSubContributionCreation(self._target)
        pars = {"postURL": urlHandlers.UHContribCreateSubCont.getURL(self._contrib)}
        params.update(pars)
        return wc.getHTML(params)


#---------------------------------------------------------------------------


class WContributionDataModificationBoard(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        return vars


class WContributionDataModificationType(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        return vars


class WContributionDataModification(wcomponents.WTemplated):

    def __init__(self, contribution, conf, rh=None):
        self._contrib = contribution
        self._owner = self._contrib.getOwner()
        self._conf = conf
        self._rh = rh

    def _getTypeItemsHTML(self):
        res = ["""<option value=""></option>"""]
        conf = self._contrib.getConference()
        for type in conf.getContribTypeList():
            selected = ""
            if self._contrib.getType() == type:
                selected = " selected"
            res.append("""<option value=%s%s>%s</option>""" % (
                quoteattr(str(type.getId())), selected,
                self.htmlText(type.getName())))
        return "".join(res)

    def _getAdditionalFieldsData(self):
        fields = self._contrib.getConference().getAbstractMgr().getAbstractFieldsMgr().getFields()
        fieldDict = {}

        for field in fields:
            f_id = "f_" + field.getId()
            fieldDict[f_id] = self._contrib.getField(field.getId())

        return fieldDict

    def getContribId(self):
        if isinstance(self._owner, conference.Session):
            return "s" + self._owner.id + "c" + self._contrib.id
        else:
            return "c" + self._contrib.id

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        defaultDefinePlace = defaultDefineRoom = ""
        defaultInheritPlace = defaultInheritRoom = "checked"
        locationName, locationAddress, roomName, defaultExistRoom = "", "", "", ""

        vars["conference"] = self._conf
        vars["boardNumber"] = quoteattr(str(self._contrib.getBoardNumber()))
        vars["contrib"] = self._contrib
        vars["title"] = quoteattr(self._contrib.getTitle())
        vars["description"] = self.htmlText(self._contrib.getDescription())
        vars["additionalFields"] = self._contrib.getConference().getAbstractMgr().getAbstractFieldsMgr().getFields()
        vars["fieldDict"] = self._getAdditionalFieldsData()
        vars["day"] = ""
        vars["month"] = ""
        vars["year"] = ""
        vars["sHour"] = ""
        vars["sMinute"] = ""
        sDate = self._contrib.getStartDate()
        if sDate is not None:
            vars["day"] = quoteattr(str(sDate.day))
            vars["month"] = quoteattr(str(sDate.month))
            vars["year"] = quoteattr(str(sDate.year))
            vars["sHour"] = quoteattr(str(sDate.hour))
            vars["sMinute"] = quoteattr(str(sDate.minute))
        if self._contrib.getStartDate():
            vars["dateTime"] = formatDateTime(self._contrib.getAdjustedStartDate())
        else:
            vars["dateTime"] = ""
        vars["duration"] = self._contrib.getDuration().seconds / 60
        if self._contrib.getDuration() is not None:
            vars["durationHours"] = quoteattr(str((datetime(1900, 1, 1) + self._contrib.getDuration()).hour))
            vars["durationMinutes"] = quoteattr(str((datetime(1900, 1, 1) + self._contrib.getDuration()).minute))
        if self._contrib.getOwnLocation():
            defaultDefinePlace = "checked"
            defaultInheritPlace = ""
            locationName = self._contrib.getLocation().getName()
            locationAddress = self._contrib.getLocation().getAddress()

        if self._contrib.getOwnRoom():
            defaultDefineRoom = "checked"
            defaultInheritRoom = ""
            defaultExistRoom = ""
            roomName = self._contrib.getRoom().getName()
        vars["defaultInheritPlace"] = defaultInheritPlace
        vars["defaultDefinePlace"] = defaultDefinePlace
        vars["confPlace"] = ""
        confLocation = self._owner.getLocation()
        if self._contrib.isScheduled():
            confLocation = self._contrib.getSchEntry().getSchedule().getOwner().getLocation()
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
        rx = []
        roomsexist = self._conf.getRoomList()
        roomsexist.sort()
        for room in roomsexist:
            sel = ""
            rx.append("""<option value=%s%s>%s</option>""" % (quoteattr(str(room)),
                                                              sel, self.htmlText(room)))
        vars["roomsexist"] = "".join(rx)
        if self._contrib.isScheduled():
            confRoom = self._contrib.getSchEntry().getSchedule().getOwner().getRoom()
        if self._contrib.getSession() and not self._contrib.getConference().getEnableSessionSlots():
            confRoom = self._contrib.getSession().getRoom()
        if confRoom:
            vars["confRoom"] = confRoom.getName()
        vars["roomName"] = quoteattr(roomName)
        vars["parentType"] = "conference"
        if self._contrib.getSession() is not None:
            vars["parentType"] = "session"
            if self._contrib.isScheduled() and self._contrib.getConference().getEnableSessionSlots():
                vars["parentType"] = "session slot"
        vars["postURL"] = urlHandlers.UHContributionDataModif.getURL(self._contrib)
        vars["types"] = self._getTypeItemsHTML()
        vars["keywords"] = self._contrib.getKeywords()
        import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
        wr = webFactoryRegistry.WebFactoryRegistry()
        wf = wr.getFactory(self._conf)
        if wf is not None:
            type = wf.getId()
        else:
            type = "conference"
        if type == "conference":
            vars["Type"] = WContributionDataModificationType().getHTML(vars)
            vars["Board"] = WContributionDataModificationBoard().getHTML(vars)
        else:
            vars["Type"] = ""
            vars["Board"] = ""

        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["useRoomBookingModule"] = minfo.getRoomBookingModuleActive()
        if self._contrib.getSession():
            vars["sessionType"] = self._contrib.getSession().getScheduleType()
        else:
            vars["sessionType"] = 'none'
        return vars


class WPEditData(WPContribModifMain):

    def _getTabContent( self, params ):
        wc = WContributionDataModification(self._target, self._conf)
        return wc.getHTML()


class WPContributionDeletion( WPContributionModifTools ):

    def _getTabContent( self, params ):
        wc = wcomponents.WContributionDeletion()
        return wc.getHTML({
                'contribList': [self._target],
                'postURL': urlHandlers.UHContributionDelete.getURL(self._target)
                })


class WPContributionReportNumberEdit(WPContributionModifBase):

    def __init__(self, rh, contribution, reportNumberSystem):
        WPContributionModifBase.__init__(self, rh, contribution)
        self._reportNumberSystem=reportNumberSystem

    def _getTabContent( self, params):
        wc=wcomponents.WModifReportNumberEdit(self._target, self._reportNumberSystem, "contribution")
        return wc.getHTML()


class WContributionICalExport(WICalExportBase):

    def __init__(self, contrib, user):
        self._contrib = contrib
        self._user = user

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["target"] = vars["Contribution"] = vars["item"] = self._contrib
        vars["urlICSFile"] =  urlHandlers.UHContribToiCal.getURL(self._contrib)
        vars.update(self._getIcalExportParams(self._user, '/export/event/%s/contribution/%s.ics' % \
                                              (self._contrib.getConference().getId(), self._contrib.getId())))

        return vars
