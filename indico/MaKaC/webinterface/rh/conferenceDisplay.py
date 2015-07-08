# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from datetime import datetime
from flask import session
import os
import pytz

import MaKaC.common.info as info
import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.rh.conferenceBase as conferenceBase
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.displayMgr as displayMgr
import MaKaC.webinterface.internalPagesMgr as internalPagesMgr
import MaKaC.user as user
import MaKaC.webinterface.mail as mail
from MaKaC.webinterface.pages.errors import WPError404
import MaKaC.conference as conference
from indico.core.config import Config
from MaKaC.webinterface.rh.base import RHDisplayBaseProtected
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.errors import MaKaCError, NoReportError, NotFoundError
from MaKaC.PDFinterface.conference import TimeTablePlain, AbstractBook, SimplifiedTimeTablePlain, TimetablePDFFormat
from MaKaC.common.contribPacker import ConferencePacker, ZIPFileHandler
import zipfile
from cStringIO import StringIO
from MaKaC.i18n import _

import MaKaC.common.timezoneUtils as timezoneUtils
from reportlab.platypus.doctemplate import LayoutError
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename

from indico.core import signals
from indico.modules.events.api import CategoryEventHook
from indico.util.i18n import set_best_lang
from indico.util.signals import values_from_signal
from indico.web.http_api.metadata.serializer import Serializer
from indico.web.flask.util import send_file


class RHConferenceAccessKey( conferenceBase.RHConferenceBase ):

    _isMobile = False

    def _checkParams(self, params):
        conferenceBase.RHConferenceBase._checkParams(self, params)
        self._accesskey = params.get("accessKey", "").strip()
        self._doNotSanitizeFields.append("accessKey")

    def _process(self):
        access_keys = session.setdefault("accessKeys", {})
        access_keys[self._conf.getUniqueId()] = self._accesskey
        session.modified = True
        url = urlHandlers.UHConferenceDisplay.getURL(self._conf)
        self._redirect(url)


class RHConferenceBaseDisplay( RHConferenceBase, RHDisplayBaseProtected ):

    def _checkParams( self, params ):
        RHConferenceBase._checkParams( self, params )

    def _checkProtection(self):
        RHDisplayBaseProtected._checkProtection(self)


class RHConferenceDisplay(RHConferenceBaseDisplay):
    _uh = urlHandlers.UHConferenceDisplay

    def _checkProtection(self):
        # check users allowed by plugins
        if any(values_from_signal(signals.event.has_read_access.send(self._conf, user=session.user))):
            return
        RHConferenceBaseDisplay._checkProtection(self)

    def _process( self ):
        params = self._getRequestParams()
        #set default variables
        if not self._reqParams.has_key("showDate"):
            self._reqParams["showDate"] = "all"
        if not self._reqParams.has_key("showSession"):
            self._reqParams["showSession"] = "all"
        if not self._reqParams.has_key("detailLevel"):
            self._reqParams["detailLevel"] = "contribution"
        #get default/selected view
        view = "static"
        wf = self.getWebFactory()
        if wf != None:
            type = self.getWebFactory().getId()
        else:
            type = "conference"
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        if self._reqParams.has_key("view"):
            view = self._reqParams["view"]
        else:
            view = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).getDefaultStyle()
            # if no default view was attributed, then get the configuration default
            if view == "" or not styleMgr.existsStyle(view):
                view =styleMgr.getDefaultStyleForEventType( type )
                displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).setDefaultStyle( view )
        isLibxml = True
        warningText = ""
        try:
            import lxml
        except:
            isLibxml = False

        # create the html factory
        if type == "conference":
            if params.get("ovw", False):
                p = conferences.WPConferenceDisplay( self, self._target )
            else:
                self._page = None
                intPagesMgr=internalPagesMgr.InternalPagesMgrRegistery().getInternalPagesMgr(self._target)
                for page in intPagesMgr.getPagesList():
                    if page.isHome():
                        self._page = page
                if not self._page:
                    p = conferences.WPConferenceDisplay( self, self._target )
                else:
                    p = conferences.WPInternalPageDisplay(self,self._target, self._page)
        elif view in styleMgr.getXSLStyles():
            if not isLibxml:
                warningText = "lxml needs to be installed if you want to use a stylesheet-driven display - switching to static display"
            self._responseUtil.content_type = 'text/xml'
            p = conferences.WPXSLConferenceDisplay( self, self._target, view, type, self._reqParams )
        elif view != "static":
            p = conferences.WPTPLConferenceDisplay( self, self._target, view, type, self._reqParams )
        else:
            if wf != None:
                p = wf.getConferenceDisplayPage( self, self._target, self._reqParams )
            else:
                p = conferences.WPConferenceDisplay( self, self._target )

        return warningText + p.display(**params)


class RHRelativeEvent(RHConferenceBaseDisplay):
    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._which = params['which']

    def _process(self):
        evt = self._conf.getOwner().getRelativeEvent(self._which, conf=self._conf)
        if evt:
            self._redirect(urlHandlers.UHConferenceDisplay.getURL(evt))
        else:
            return WPError404(self, urlHandlers.UHConferenceDisplay.getURL(self._conf)).display()


class RHConferenceOtherViews(RHConferenceBaseDisplay):
    """
    this class is for the conference type objects only
    it is an alternative to the standard TimeTable view
    """
    _uh = urlHandlers.UHConferenceOtherViews

    def _process( self ):
        #set default variables
        if not self._reqParams.has_key("showDate"):
            self._reqParams["showDate"] = "all"
        if not self._reqParams.has_key("showSession"):
            self._reqParams["showSession"] = "all"
        if not self._reqParams.has_key("detailLevel"):
            self._reqParams["detailLevel"] = "contribution"
        #get default/selected view
        view = "standard"
        type = "conference"
        styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
        isLibxml = True
        try:
            import lxml
        except:
            isLibxml = False
        if self._reqParams.has_key("view"):
            view = self._reqParams["view"]
        else:
            view = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).getDefaultStyle()
            # if no default view was attributed, then get the configuration default
            if view == "":
                view =styleMgr.getDefaultStyleForEventType(type)
                displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).setDefaultStyle(view)
        # create the html factory
        if view in styleMgr.getXSLStyles() and isLibxml:
            p = conferences.WPXSLConferenceDisplay(self, self._target, view, type, self._reqParams)
        elif view != "static":
            p = conferences.WPTPLConferenceDisplay(self, self._target, view, type, self._reqParams)
        else:
            p = conferences.WPMeetingTimeTable(self, self._target, "parallel", "meeting", self._reqParams)
        # generate the html
        if view == "xml" and self._reqParams.get('fr') == 'no':
            self._responseUtil.content_type = 'text/xml'
        return p.display()


class RHConferenceGetLogo(RHConferenceBase):

    def _process(self):
        logo = self._target.getLogo()
        if not logo:
            raise MaKaCError(_("This event does not have a logo"))
        return send_file(logo.getFileName(), logo.getFilePath(), logo.getFileType(), no_cache=False, conditional=True)


class RHConferenceGetCSS(RHConferenceBase):

    """
    CSS which is used just for a conference.
    """

    def _process(self):
        sm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getStyleManager()
        css = sm.getLocalCSS()
        if css:
            return send_file(css.getFileName(), css.getFilePath(), mimetype='text/css', no_cache=False, conditional=True)
        return ""


class RHConferenceGetPic(RHConferenceBaseDisplay):

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._picId = params.get("picId", "")

    def _process(self):
        im = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getImagesManager()
        if im.getPic(self._picId):
            pic = im.getPic(self._picId).getLocalFile()
            return send_file(pic.getFileName(), pic.getFilePath(), pic.getFileType())
        else:
            self._responseUtil.status = 404
            return WPError404(self, urlHandlers.UHConferenceDisplay.getURL(self._conf)).display()


class RHConferenceEmail(RHConferenceBaseDisplay, base.RHProtected):
    _uh = urlHandlers.UHConferenceEmail

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._auth = "authorId" in params
        self._chair = "chairId" in params
        if params.has_key("contribId"):
            contrib = self._conf.getContributionById(params.get("contribId",""))
        if self._chair:
            chairid=params.get("chairId","")
            chair = self._conf.getChairById(chairid)
            if chair == None:
                raise NotFoundError(_("The chair you try to email does not exist."))
            self._emailto = chair
        if self._auth:
            authid = params.get("authorId", "")
            if not contrib:
                raise MaKaCError(_("The author's contribution does not exist anymore."))
            author = contrib.getAuthorById(authid)
            if author == None:
                raise NotFoundError(_("The author you try to email does not exist."))
            self._emailto = author

    def _process(self):
        postURL = urlHandlers.UHConferenceSendEmail.getURL(self._emailto)
        p=conferences.WPEMail(self, self._target)
        return p.display(emailto=[self._emailto], postURL=postURL)

class RHConferenceSendEmail (RHConferenceBaseDisplay, base.RHProtected):
    _uh = urlHandlers.UHConferenceSendEmail

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams( self, params )
        if "contribId" in params:
            contrib = self._conf.getContributionById(params.get("contribId",""))
        if "chairId" in params:
            chairid=params.get("chairId","")
            self._to = self._conf.getChairById(chairid).getEmail()
        if "authorId" in params:
            authid = params.get("authorId", "")
            self._to = contrib.getAuthorById(authid).getEmail()
        fromId = params.get("from","")
        self._from = (user.AvatarHolder()).getById(fromId).getEmail()
        self._cc = self._from
        self._subject=params.get("subject","")
        self._body = params.get("body","")
        self._send = params.has_key("OK")

    def _process(self):
        if self._send:
            mail.personMail.send(self._to, self._cc, self._from,self._subject,self._body)
            p = conferences.WPSentEmail(self, self._target)
            return p.display()
        else:
            self._redirect(urlHandlers.UHConferenceDisplay.getURL(self._conf))


class RHConferenceProgram(RHConferenceBaseDisplay):
    _uh = urlHandlers.UHConferenceProgram

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._xs = self._normaliseListParam(params.get("xs", []))

    def _process(self):
        p = conferences.WPConferenceProgram(self, self._target)
        return p.display(xs=self._xs)


class RHConferenceProgramPDF(RHConferenceBaseDisplay):

    def _process(self):
        set_best_lang()  # prevents from having a _LazyString when generating a pdf without session.lang set
        tz = timezoneUtils.DisplayTZ(self._aw, self._target).getDisplayTZ()
        filename = "%s - Programme.pdf" % self._target.getTitle()
        from MaKaC.PDFinterface.conference import ProgrammeToPDF
        pdf = ProgrammeToPDF(self._target, tz=tz)
        return send_file(filename, StringIO(pdf.getPDFBin()), 'PDF')


class RHConferenceTimeTable(RHConferenceBaseDisplay):
    _uh = urlHandlers.UHConferenceTimeTable

    def _process( self ):
        defStyle = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).getDefaultStyle()
        if defStyle in ["", "static", "parallel"]:
            p = conferences.WPConferenceTimeTable( self, self._target )
            return p.display( **self._getRequestParams() )
        else:
            url = urlHandlers.UHConferenceOtherViews.getURL( self._conf )
            url.addParam("view", defStyle)
            self._redirect(url)


class RHTimeTablePDF(RHConferenceTimeTable):

    fontsizes = ['xxx-small', 'xx-small', 'x-small', 'smaller', 'small', 'normal', 'large', 'larger']

    def _checkParams(self,params):
        RHConferenceTimeTable._checkParams(self,params)
        self._showSessions=self._normaliseListParam(params.get("showSessions",[]))
        if "all" in self._showSessions:
            self._showSessions.remove("all")
        self._showDays=self._normaliseListParam(params.get("showDays",[]))
        if "all" in self._showDays:
            self._showDays.remove("all")
        self._sortingCrit=None
        if params.has_key("sortBy") and params["sortBy"].strip()!="":
            self._sortingCrit=contribFilters.SortingCriteria([params.get( "sortBy", "number").strip()])
        self._pagesize = params.get('pagesize','A4')
        self._fontsize = params.get('fontsize','normal')
        try:
            self._firstPageNumber = int(params.get('firstPageNumber','1'))
        except ValueError:
            self._firstPageNumber = 1
        self._showSpeakerAffiliation = False
        if params.has_key("showSpeakerAffiliation"):
            self._showSpeakerAffiliation = True
        # Keep track of the used layout for getting back after cancelling
        # the export.
        self._view = params.get("view", displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._target).getDefaultStyle())

    def _reduceFontSize( self ):
        index = self.fontsizes.index(self._fontsize)
        if index > 0:
            self._fontsize = self.fontsizes[index-1]
            return True
        return False

    def _process(self):
        set_best_lang()  # prevents from having a _LazyString when generating a pdf without session.lang set
        tz = timezoneUtils.DisplayTZ(self._aw,self._target).getDisplayTZ()
        params = self._getRequestParams()
        ttPDFFormat=TimetablePDFFormat(params)

        # Choose action depending on the button pressed
        if params.has_key("cancel"):
            # If the export is cancelled, redirect to the display
            # page
            url = urlHandlers.UHConferenceDisplay.getURL(self._conf)
            url.addParam("view", self._view)
            self._redirect(url)
        else :
            retry = True
            while retry:
                if params.get("typeTT","normalTT")=="normalTT":
                    filename = "timetable.pdf"
                    pdf = TimeTablePlain(self._target,self.getAW(),
                            showSessions=self._showSessions,showDays=self._showDays,
                            sortingCrit=self._sortingCrit, ttPDFFormat=ttPDFFormat,
                            pagesize = self._pagesize, fontsize = self._fontsize,
                            firstPageNumber = self._firstPageNumber,
                            showSpeakerAffiliation = self._showSpeakerAffiliation)
                else:
                    filename = "SimplifiedTimetable.pdf"
                    pdf = SimplifiedTimeTablePlain(self._target,self.getAW(),
                        showSessions=self._showSessions,showDays=self._showDays,
                        sortingCrit=self._sortingCrit, ttPDFFormat=ttPDFFormat,
                        pagesize = self._pagesize, fontsize = self._fontsize)
                try:
                    data=pdf.getPDFBin()
                    retry = False
                except LayoutError, e:
                    if not self._reduceFontSize():
                        raise MaKaCError("Error in PDF generation - One of the paragraphs does not fit on a page")
                except Exception:
                    raise

    ##        tries = 5
    ##        while tries:
    ##            if params.get("typeTT","normalTT")=="normalTT":
    ##                filename = "timetable.pdf"
    ##                pdf = TimeTablePlain(self._target,self.getAW(),
    ##                        showSessions=self._showSessions,showDays=self._showDays,
    ##                        sortingCrit=self._sortingCrit, ttPDFFormat=ttPDFFormat,
    ##                        pagesize = self._pagesize, fontsize = self._fontsize, firstPageNumber = self._firstPageNumber, tz=tz)
    ##            else:
    ##                filename = "SimplifiedTimetable.pdf"
    ##                pdf = SimplifiedTimeTablePlain(self._target,self.getAW(),
    ##                    showSessions=self._showSessions,showDays=self._showDays,
    ##                    sortingCrit=self._sortingCrit, ttPDFFormat=ttPDFFormat,
    ##                    pagesize = self._pagesize, fontsize = self._fontsize, tz=tz)
    ##            try:
    ##                data=pdf.getPDFBin()
    ##                tries = 0
    ##            except LayoutError, e:
    ##                if self._reduceFontSize():
    ##                    tries -= 1
    ##                else:
    ##                    tries = 0
    ##                    raise MaKaCError(str(e))

            return send_file(filename, StringIO(data), 'PDF')

class RHTimeTableCustomizePDF(RHConferenceTimeTable):

    def _checkParams(self,params):
        RHConferenceTimeTable._checkParams(self,params)
        self._cancel = params.has_key("cancel")
        self._view = params.get("view", "standard")

    def _process(self):
        if self._target.getType() =="simple_event":
            raise NoReportError(_("Lectures have no timetable therefore one cannot generate a timetable PDF."))

        wf = self.getWebFactory()
        if wf != None:
            p=wf.getTimeTableCustomizePDF(self, self._target, self._view)
        else:
            p=conferences.WPTimeTableCustomizePDF(self, self._target)
        return p.display(**self._getRequestParams())


class _HideWithdrawnFilterField(filters.FilterField):
    """
    """
    _id = "hide_withdrawn"

    def __init__(self,conf,values):
        pass

    def satisfies(self,contribution):
        """
        """
        return not isinstance(contribution.getCurrentStatus(),conference.ContribStatusWithdrawn)


class ContributionsFilterCrit(filters.FilterCriteria):
    _availableFields = { \
        contribFilters.TypeFilterField.getId():contribFilters.TypeFilterField, \
        contribFilters.TrackFilterField.getId():contribFilters.TrackFilterField, \
        contribFilters.SessionFilterField.getId():contribFilters.SessionFilterField, \
        _HideWithdrawnFilterField.getId(): _HideWithdrawnFilterField
                }


class RHContributionList( RHConferenceBaseDisplay ):
    _uh = urlHandlers.UHContributionList

    @staticmethod
    def create_filter(conf, params, filterUsed=False):
        filter = {"hide_withdrawn": True}
        ltypes = ltracks = lsessions = []
        if not filterUsed:
            for type in conf.getContribTypeList():
                ltypes.append( type.getId() )
            for track in conf.getTrackList():
                ltracks.append( track.getId() )
            for session in conf.getSessionList():
                lsessions.append( session.getId() )

        filter["type"] = params.get("selTypes", ltypes)
        filter["track"] = params.get("selTracks", ltracks)
        filter["session"] = params.get("selSessions", lsessions)
        return ContributionsFilterCrit(conf,filter)

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )

        # Filtering
        filterUsed = params.get("filter","no") == "yes"
        self._filterText =  params.get("filterText","")
        self._filterCrit = self.create_filter(self._conf, params, filterUsed)

        typeShowNoValue, trackShowNoValue, sessionShowNoValue = True, True, True
        if filterUsed:
            if self._conf.getContribTypeList():
                typeShowNoValue =  params.has_key("typeShowNoValue")
            if self._conf.getTrackList():
                trackShowNoValue =  params.has_key("trackShowNoValue")
            if self._conf.getSessionList():
                sessionShowNoValue =  params.has_key("sessionShowNoValue")
        self._filterCrit.getField("type").setShowNoValue( typeShowNoValue )
        self._filterCrit.getField("track").setShowNoValue( trackShowNoValue )
        self._filterCrit.getField("session").setShowNoValue( sessionShowNoValue )


    def _process( self ):
        p = conferences.WPContributionList( self, self._target )
        return p.display(filterCrit = self._filterCrit, filterText=self._filterText)


class RHAuthorIndex(RHConferenceBaseDisplay):
    _uh=urlHandlers.UHConfAuthorIndex

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )

    def _process(self):
        p=conferences.WPAuthorIndex(self,self._target)
        return p.display()

class RHSpeakerIndex(RHConferenceBaseDisplay):
    _uh=urlHandlers.UHConfSpeakerIndex

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )

    def _process(self):
        p=conferences.WPSpeakerIndex(self,self._target)
        return p.display()

class RHMyStuff(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuff

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        p=conferences.WPMyStuff(self,self._target)
        return p.display()

class RHConfMyStuffMySessions(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuffMySessions

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        ls = set(self._conf.getCoordinatedSessions(self._aw.getUser())) | \
             set(self._conf.getManagedSession(self._aw.getUser()))
        if len(ls) == 1:
            self._redirect(urlHandlers.UHSessionModification.getURL(ls.pop()))
        else:
            p = conferences.WPConfMyStuffMySessions(self, self._target)
            return p.display()

class RHConfMyStuffMyContributions(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuffMyContributions

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        p=conferences.WPConfMyStuffMyContributions(self,self._target)
        return p.display()

class RHConfMyStuffMyTracks(RHConferenceBaseDisplay,base.RHProtected):
    _uh=urlHandlers.UHConfMyStuffMyTracks

    def _checkProtection(self):
        base.RHProtected._checkProtection(self)

    def _process(self):
        ltracks = self._target.getCoordinatedTracks(self._aw.getUser())

        if len(ltracks) == 1:
            self._redirect(urlHandlers.UHTrackModifAbstracts.getURL(ltracks[0]))
        else:
            p = conferences.WPConfMyStuffMyTracks(self, self._target)
            return p.display()

class RHContributionListToPDF(RHConferenceBaseDisplay):

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._contribs = []
        for id in contribIds:
            contrib = self._conf.getContributionById(id)
            if contrib.canAccess(self.getAW()):
                self._contribs.append(contrib)

    def _process( self ):
        tz = timezoneUtils.DisplayTZ(self._aw,self._conf).getDisplayTZ()
        filename = "Contributions.pdf"
        if not self._contribs:
            return "No contributions to print"
        from MaKaC.PDFinterface.conference import ContribsToPDF
        pdf = ContribsToPDF(self._conf, self._contribs)

        return send_file(filename, pdf.generate(), 'PDF')


class RHAbstractBook(RHConferenceBaseDisplay):
    _uh=urlHandlers.UHConfAbstractBook

    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        self._noCache = params.get('cache') == '0'

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        if not self._conf.getAbstractMgr().isActive() or not self._conf.hasEnabledSection("cfa"):
            raise MaKaCError( _("The Call For Abstracts was disabled by the conference managers"))

    def _getCacheFileName(self):
        dir = os.path.join(Config().getInstance().getXMLCacheDir(), "abstract_books")
        if not os.path.exists(dir):
            os.makedirs(dir)
        return os.path.join(dir, '%s.pdf' % self._conf.getId())

    def _process(self):
        boaConfig = self._conf.getBOAConfig()
        pdfFilename = "%s - Book of abstracts.pdf" % cleanHTMLHeaderFilename(self._target.getTitle())
        cacheFile = self._getCacheFileName()
        if os.path.isfile(cacheFile):
            mtime = pytz.utc.localize(datetime.utcfromtimestamp(os.path.getmtime(cacheFile)))
        else:
            mtime = None

        if boaConfig.isCacheEnabled() and not self._noCache and mtime and mtime > boaConfig.lastChanged:
            return send_file(pdfFilename, cacheFile, 'PDF')
        else:
            tz = timezoneUtils.DisplayTZ(self._aw, self._target).getDisplayTZ()
            pdf = AbstractBook(self._target, self.getAW(), tz=tz)
            fname = pdf.generate()

            with open(fname, 'rb') as f:
                data = f.read()
            with open(cacheFile, 'wb') as f:
                f.write(data)

            return send_file(pdfFilename, cacheFile, 'PDF')


class RHConfParticipantsRefusal(RHConferenceBaseDisplay):
    _uh = urlHandlers.UHConfParticipantsRefusal

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams(self, params )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process(self):
        params = self._getRequestParams()
        participantId = params["participantId"]
        status = self._conf.getParticipation().getParticipantById(participantId).getStatus()
        if status == 'accepted':
            raise NoReportError(_('You have already accepted the invitation.'))
        elif status == 'rejected':
            raise NoReportError(_('You have already rejected the invitation.'))
        if self._cancel:
            url = urlHandlers.UHConferenceDisplay.getURL(self._conf)
            self._redirect(url)
        elif self._confirm:
            participant = self._conf.getParticipation().getParticipantById(participantId)
            participant.setStatusRefused()
            url = urlHandlers.UHConferenceDisplay.getURL(self._conf)
            self._redirect(url)
        else:
            return conferences.WPConfModifParticipantsRefuse(self, self._conf).display(**params)


class RHConfParticipantsInvitation(RHConferenceBaseDisplay):
    _uh = urlHandlers.UHConfParticipantsInvitation

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams(self, params )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process( self ):
        params = self._getRequestParams()
        participantId = params["participantId"]
        status = self._conf.getParticipation().getParticipantById(participantId).getStatus()
        if status == 'accepted':
            raise NoReportError(_('You have already accepted the invitation.'))
        elif status == 'rejected':
            raise NoReportError(_('You have already rejected the invitation.'))
        if self._cancel:
            if not self._conf.getParticipation().setParticipantRejected(participantId):
                raise NoReportError("It seems you have been withdrawn from the list of invited participants")
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
            self._redirect( url )
        elif self._confirm:
            if not self._conf.getParticipation().setParticipantAccepted(participantId):
                raise NoReportError("It seems you have been withdrawn from the list of invited participants")
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
            self._redirect( url )
        else:
            return conferences.WPConfModifParticipantsInvite( self, self._conf ).display(**params)


class RHConferenceToiCal(RHConferenceBaseDisplay):

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._detailLevel = params.get("detail","events")

    def _process(self):
        filename = "%s-Event.ics" % self._target.getTitle()

        hook = CategoryEventHook({'detail': self._detailLevel}, 'event',
                                 {'idlist': self._conf.getId(), 'dformat': 'ics'})
        res = hook(self.getAW())
        resultFossil = {'results': res[0]}

        serializer = Serializer.create('ics')
        return send_file(filename, StringIO(serializer(resultFossil)), 'ICAL')


class RHConferenceToXML(RHConferenceBaseDisplay):

    def _checkParams( self, params ):
        RHConferenceBaseDisplay._checkParams( self, params )
        self._xmltype = params.get("xmltype","standard")

    def _process(self):
        filename = "%s - Event.xml" % self._target.getTitle()
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("event")
        outgen.confToXML(self._target.getConference(),0,0,1)
        xmlgen.closeTag("event")
        return send_file(filename, StringIO(xmlgen.getXml()), 'XML')


class RHConferenceToMarcXML(RHConferenceBaseDisplay):

    def _process( self ):
        filename = "%s - Event.xml"%cleanHTMLHeaderFilename(self._target.getTitle())
        from MaKaC.common.xmlGen import XMLGen
        from MaKaC.common.output import outputGenerator
        xmlgen = XMLGen()
        xmlgen.initXml()
        outgen = outputGenerator(self.getAW(), xmlgen)
        xmlgen.openTag("marc:record", [["xmlns:marc","http://www.loc.gov/MARC21/slim"],["xmlns:xsi","http://www.w3.org/2001/XMLSchema-instance"],["xsi:schemaLocation", "http://www.loc.gov/MARC21/slim http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd"]])
        outgen.confToXMLMarc21(self._target.getConference())
        xmlgen.closeTag("marc:record")
        return send_file(filename, StringIO(xmlgen.getXml()), 'XML')


class RHInternalPageDisplay(RHConferenceBaseDisplay):
    _uh = urlHandlers.UHInternalPageDisplay

    def _checkParams(self, params):
        self._page = None
        RHConferenceBaseDisplay._checkParams(self, params)

        if 'pageId' in params:
            pageId = params.get("pageId")
            intPagesMgr = internalPagesMgr.InternalPagesMgrRegistery().getInternalPagesMgr(self._conf)
            self._page = intPagesMgr.getPageById(pageId)
            self._target = self._conf

            if self._page is None:
                raise NotFoundError(_("The web page you are trying to access does not exist"))
        else:
            raise NotFoundError(_("The web page you are trying to access does not exist"))

    def _process(self):
        p = conferences.WPInternalPageDisplay(self, self._conf, self._page)
        return p.display()


class RHConferenceLatexPackage(RHConferenceBaseDisplay):

    def _process(self):
        filename = "%s-BookOfAbstracts.zip" % self._target.getTitle()
        zipdata = StringIO()
        zip = zipfile.ZipFile(zipdata, "w")
        for cont in self._target.getContributionList():
            f = []
            f.append("""\\section*{%s}"""%cont.getTitle())
            f.append(" ")
            l = []
            affil = {}
            i = 1
            for pa in cont.getPrimaryAuthorList():
                if pa.getAffiliation() in affil.keys():
                    num = affil[pa.getAffiliation()]
                else:
                    affil[pa.getAffiliation()] = i
                    num = i
                    i += 1

                l.append("""\\noindent \\underline{%s}$^%d$"""%(pa.getFullName(), num))

            for ca in cont.getCoAuthorList():
                if ca.getAffiliation() in affil.keys():
                    num = affil[ca.getAffiliation()]
                else:
                    affil[ca.getAffiliation()] = i
                    num = i
                    i += 1
                l.append("""%s$^%d$"""%(ca.getFullName(), num))

            f.append(",\n".join(l))
            f.append("\n")
            l = []
            for key in affil.keys():
                l.append("""$^%d$%s"""%(affil[key], key))
            f.append("\\noindent " + ",\n".join(l))
            f.append("\n")
            f.append("""\\noindent %s"""%cont.getDescription())
            zip.writestr("contribution-%s"%cont.getId(), "\n".join(f))
        zip.close()
        zipdata.seek(0)

        return send_file(filename, zipdata, 'ZIP', inline=False)
