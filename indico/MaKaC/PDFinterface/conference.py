# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import re
import types
from copy import deepcopy
from datetime import timedelta
from itertools import takewhile
from operator import attrgetter

from PIL import Image
from sqlalchemy import cast, Date
from qrcode import QRCode, constants

from MaKaC.PDFinterface.base import escape
from pytz import timezone
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.rl_config import defaultPageSize
from reportlab.platypus import Table, TableStyle
from reportlab.pdfgen import canvas
from MaKaC.common.timezoneUtils import DisplayTZ,nowutc
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.review as review
import MaKaC.conference as conference
from MaKaC.badge import BadgeTemplateItem
from MaKaC.poster import PosterTemplateItem
from MaKaC.PDFinterface.base import (PDFLaTeXBase, PDFBase, PDFWithTOC, Paragraph, Spacer, PageBreak, FileDummy,
                                     setTTFonts, PDFSizes, modifiedFontSize)
from MaKaC.webinterface.pages.tracks import (
    AbstractStatusTrackViewFactory,
    _ASTrackViewPFOT,
    _ASTrackViewPA,
    _ASTrackViewDuplicated,
    _ASTrackViewMerged,
    _ASTrackViewIC,
    _ASTrackViewAcceptedForOther
)
from MaKaC.webinterface.common.abstractStatusWrapper import AbstractStatusList
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.errors import NoReportError
from reportlab.lib.pagesizes import landscape, A4
from MaKaC.badgeDesignConf import BadgeDesignConfiguration
from MaKaC.posterDesignConf import PosterDesignConfiguration
from MaKaC.webinterface.common.tools import strip_ml_tags
from MaKaC.i18n import _
from MaKaC.common import utils

from indico.core.config import Config
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.modules.events.util import create_event_logo_tmp_file
from indico.util import json
from indico.util.date_time import format_date, format_datetime, format_time, format_human_timedelta, as_utc
from indico.util.i18n import i18nformat
from indico.util.string import html_color_to_rgb


styles = getSampleStyleSheet()


def extract_affiliations(contrib):
    affiliations = dict()

    def enumerate_affil(person_links):
        auth_list = []

        for person_link in person_links:
            person = person_link.person
            affil = person.affiliation
            if affil and affil not in affiliations:
                affiliations[affil] = len(affiliations) + 1
            auth_list.append((person_link, affiliations[affil] if affil else None))
        return auth_list

    authors = enumerate_affil(contrib.primary_authors)
    coauthors = enumerate_affil(contrib.secondary_authors)
    return affiliations, authors, coauthors


class ProgrammeToPDF(PDFBase):

    def __init__(self, conf, doc=None, story=None, tz=None):
        self._conf = conf
        if not tz:
            self._tz = self._conf.getTimezone()
        else:
            self._tz = tz
        PDFBase.__init__(self, doc, story)
        self._title = _("Conference Scientific Programme")

    def firstPage(self, c, doc):
        c.saveState()

        height = self._drawLogo(c)

        if not height:
            height = self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT - 2*inch)

        c.setFont('Times-Bold', 15)

        height -= 2 * cm

        c.drawCentredString(self._PAGE_WIDTH/2.0, height, "%s - %s"%(self._conf.getAdjustedStartDate(self._tz).strftime("%A %d %B %Y"), self._conf.getAdjustedEndDate(self._tz).strftime("%A %d %B %Y")))
        if self._conf.getLocation():
            height-=1*cm
            c.drawCentredString(self._PAGE_WIDTH/2.0, height, escape(self._conf.getLocation().getName()))
        c.setFont('Times-Bold', 30)
        height-=6*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0, height, self._title)
        self._drawWrappedString(c, "%s / %s"%(strip_ml_tags(self._conf.getTitle()),self._title), width=inch, height=0.75*inch, font='Times-Roman', size=9, color=(0.5,0.5,0.5), align="left", maximumWidth=self._PAGE_WIDTH-3.5*inch, measurement=inch, lineSpacing=0.15)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()

    def laterPages(self, c, doc):
        c.saveState()
        self._drawWrappedString(c, "%s / %s"%(escape(strip_ml_tags(self._conf.getTitle())),self._title), width=inch, height=self._PAGE_HEIGHT-0.75*inch, font='Times-Roman', size=9, color=(0.5,0.5,0.5), align="left", maximumWidth=self._PAGE_WIDTH-3.5*inch, measurement=inch, lineSpacing=0.15)
        c.drawCentredString(self._PAGE_WIDTH/2.0, 0.75 * inch, "Page %d "%doc.page)
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()

    def getBody(self, story=None):
        if not story:
            story = self._story
        style = styles["Normal"]
        style.alignment = TA_JUSTIFY
        p = Paragraph(escape(self._conf.getProgramDescription()), style)
        story.append(p)
        story.append(Spacer(1, 0.4*inch))

        for track in self._conf.getTrackList():

            bogustext = track.getTitle()
            p = Paragraph(escape(bogustext), styles["Heading1"])
            self._story.append(p)
            bogustext = track.getDescription()
            p = Paragraph(escape(bogustext), style)
            story.append(p)
            story.append(Spacer(1, 0.4*inch))


class AbstractToPDF(PDFLaTeXBase):

    _tpl_filename = 'single_doc.tpl'

    def __init__(self, abstract, tz=None):
        super(AbstractToPDF, self).__init__()

        self._abstract = abstract
        conf = abstract.getConference()

        if tz is None:
            tz = conf.getTimezone()

        self._args.update({
            'doc_type': 'abstract',
            'abstract': abstract,
            'conf': conf,
            'tz': tz,
            'track_class': self._get_track_classification(abstract),
            'contrib_type': self._get_contrib_type(abstract),
            'fields': conf.getAbstractMgr().getAbstractFieldsMgr().getActiveFields()
        })

        logo = conf.getLogo()
        if logo:
            self._args['logo_img'] = logo.getFilePath()

    @staticmethod
    def _get_track_classification(abstract):
        status = abstract.getCurrentStatus()
        if isinstance(status, review.AbstractStatusAccepted):
            if status.getTrack() is not None:
                return escape(status.getTrack().getTitle())
        else:
            listTrack = []
            for track in abstract.getTrackListSorted():
                listTrack.append(escape(track.getTitle()))
            return "; ".join(listTrack)

    @staticmethod
    def _get_contrib_type(abstract):
        status = abstract.getCurrentStatus()
        if isinstance(status, review.AbstractStatusAccepted):
            return status.getType()
        else:
            return abstract.getContribType()


class AbstractsToPDF(PDFLaTeXBase):

    _tpl_filename = "report.tpl"

    def __init__(self, conf, abstract_ids, tz=None):
        super(AbstractsToPDF, self).__init__()
        self._conf = conf

        if tz is None:
            self._tz = conf.getTimezone()

        ab_mgr = conf.getAbstractMgr()

        abstracts = [ab_mgr.getAbstractById(aid) for aid in abstract_ids]

        self._args.update({
            'conf': conf,
            'doc_type': 'abstract',
            'title': _("Report of Abstracts"),
            'get_track_classification': AbstractToPDF._get_track_classification,
            'get_contrib_type': AbstractToPDF._get_contrib_type,
            'items': abstracts,
            'fields': conf.getAbstractMgr().getAbstractFieldsMgr().getActiveFields()
        })


class ConfManagerAbstractToPDF(AbstractToPDF):

    def __init__(self, abstract, tz=None):
        super(ConfManagerAbstractToPDF, self).__init__(abstract, tz)

        self._args.update({
            'doc_type': 'abstract_manager',
            'status': self._get_status(abstract),
            'track_judgements': self._get_track_judgements(abstract)
        })

    @staticmethod
    def _get_status(abstract):
        status = abstract.getCurrentStatus()
        #style = ParagraphStyle({})
        #style.firstLineIndent = -90
        #style.leftIndent = 90
        if isinstance(status, review.AbstractStatusDuplicated):
            original = status.getOriginal()
            return _("DUPLICATED ({0}: {1})").format(original.getId(), original.getTitle())
        elif isinstance(status, review.AbstractStatusMerged):
            target = status.getTargetAbstract()
            return _("MERGED ({0}: {1})").format(target.getId(), target.getTitle())
        else:
            return AbstractStatusList.getInstance().getCaption(status.__class__).upper()

    @staticmethod
    def _get_track_judgements(abstract):
        judgements = []

        for track in abstract.getTrackListSorted():
            status = abstract.getTrackJudgement(track)
            if isinstance(status, review.AbstractAcceptance):
                if status.getContribType() is None:
                    contribType = ""
                else:
                    contribType = status.getContribType().getName()
                st = _("Proposed to accept: {0}").format(contribType)

            elif isinstance(status, review.AbstractRejection):
                st = _("Proposed to reject")

            elif isinstance(status, review.AbstractInConflict):
                st = _("Conflict")

            elif isinstance(status, review.AbstractReallocation):
                l = []
                for track in status.getProposedTrackList():
                    l.append(track.getTitle())
                st = _("Proposed for other tracks (%s)").format(", ".join(l))

            else:
                st = ""

            judgements.append((track.getTitle(), st))
        return judgements


class ConfManagerAbstractsToPDF(AbstractsToPDF):

    def __init__(self, conf, abstract_ids, tz=None):
        super(ConfManagerAbstractsToPDF, self).__init__(conf, abstract_ids, tz)

        self._args.update({
            'doc_type': 'abstract_manager',
            'get_status': ConfManagerAbstractToPDF._get_status,
            'get_track_judgements': ConfManagerAbstractToPDF._get_track_judgements
        })


class TrackManagerAbstractToPDF(AbstractToPDF):

    def __init__(self, abstract, track, tz=None):
        super(TrackManagerAbstractToPDF, self).__init__(abstract, tz=tz)
        self._track = track

        self._args.update({
            'doc_type': 'abstract_track_manager',
            'track_view': self._get_abstract_track_view(track, abstract)
        })

    @staticmethod
    def _get_abstract_track_view(track, abstract):
        status = AbstractStatusTrackViewFactory.getStatus(track, abstract)
        comments = escape(status.getComment())
        st = status.getLabel().upper()

        if isinstance(status, _ASTrackViewPFOT):
            tracks = [(track.getId(), escape(track.getTitle())) for track in status.getProposedTrackList()]
            return (st, tracks)

        elif isinstance(status, _ASTrackViewPA):
            ctype = status.getContribType()
            conflicts = [
                (jud.getTrack().getTitle(), jud.getResponsible().getFullName())
                for jud in status.getConflicts()]
            return (st, conflicts)

        elif isinstance(status, _ASTrackViewAcceptedForOther):
            return (st, status.getTrack())

        elif isinstance(status, _ASTrackViewIC):
            return (st, None)

        elif isinstance(status, _ASTrackViewDuplicated):
            return (st, status.getOriginal())

        elif isinstance(status, _ASTrackViewMerged):
            return (st, status.getTarget())

        else:
            return (st, None)


class TrackManagerAbstractsToPDF(AbstractsToPDF):
    def __init__(self, conf, track, abstract_ids, tz=None):
        super(TrackManagerAbstractsToPDF, self).__init__(conf, abstract_ids, tz)

        self._args.update({
            'track': track,
            'doc_type': 'abstract_track_manager',
            'get_track_view': TrackManagerAbstractToPDF._get_abstract_track_view
        })


class ContribToPDF(PDFLaTeXBase):

    _tpl_filename = 'single_doc.tpl'

    def __init__(self, contrib, tz=None):
        super(ContribToPDF, self).__init__()

        event = contrib.event_new
        affiliations, author_mapping, coauthor_mapping = extract_affiliations(contrib)

        self._args.update({
            'doc_type': 'contribution',
            'affiliations': affiliations,
            'authors_affil': author_mapping,
            'coauthors_affil': coauthor_mapping,
            'contrib': contrib,
            'conf': event.as_legacy,
            'tz': tz or event.timezone,
            'fields': [f for f in event.contribution_fields if f.is_active]
        })

        if event.logo:
            self.temp_file = create_event_logo_tmp_file(event)
            self._args['logo_img'] = self.temp_file.name


class ContribsToPDF(PDFLaTeXBase):

    _table_of_contents = True
    _tpl_filename = "report.tpl"

    def __init__(self, conf, contribs, tz=None):
        super(ContribsToPDF, self).__init__()

        event = conf.as_event
        self._args.update({
            'doc_type': 'contribution',
            'title': _("Report of Contributions"),
            'conf': conf,
            'items': contribs,
            'fields': [f for f in event.contribution_fields if f.is_active],
            'url': conf.getURL(),
            'tz': tz or event.timezone
        })

        if event.logo:
            self.temp_file = create_event_logo_tmp_file(event)
            self._args['logo_img'] = self.temp_file.name


class ContributionBook(PDFLaTeXBase):

    _tpl_filename = "contribution_list_boa.tpl"

    def _sort_contribs(self, contribs, sort_by, aw):
        attr = {'boardNo': 'board_number', 'schedule': 'start_dt'}.get(sort_by, 'title')
        return sorted(contribs, key=attrgetter(attr))

    def __init__(self, conf, aw, contribs=None, tz=None, sort_by=""):
        super(ContributionBook, self).__init__()
        self._conf = conf

        event = conf.as_event
        tz = tz or event.timezone
        contribs = self._sort_contribs(contribs or event.contributions, sort_by, aw)
        affiliation_contribs = {}
        corresp_authors = {}

        for contrib in contribs:
            affiliations, author_mapping, coauthor_mapping = extract_affiliations(contrib)
            affiliation_contribs[contrib.id] = {
                'affiliations': affiliations,
                'authors_affil': author_mapping,
                'coauthors_affil': coauthor_mapping
            }

            # figure out "corresponding author(s)"
            if conf.getBOAConfig().getCorrespondingAuthor() == "submitter":
                corresp_authors[contrib.id] = [pl.person.email for pl in contrib.person_links if pl.is_submitter]
            elif conf.getBOAConfig().getCorrespondingAuthor() == "speakers":
                corresp_authors[contrib.id] = [speaker.person.email for speaker in contrib.spekaers]

        self._args.update({
            'affiliation_contribs': affiliation_contribs,
            'corresp_authors': corresp_authors,
            'contribs': contribs,
            'conf': conf,
            'tz': tz or event.timezone,
            'url': conf.getURL(),
            'fields': [f for f in event.contribution_fields if f.is_active],
            'sorted_by': sort_by,
            'aw': aw,
            'boa_text': conf.getBOAConfig().getText()
        })

        if event.logo:
            self.temp_file = create_event_logo_tmp_file(event)
            self._args['logo_img'] = self.temp_file.name


class AbstractBook(ContributionBook):

    _tpl_filename = "book_of_abstracts.tpl"
    _table_of_contents = True

    def __init__(self, conf, aw, tz=None):
        if not tz:
            tz = conf.getTimezone()

        sort_by = conf.getBOAConfig().getSortBy()
        if not sort_by.strip() or sort_by not in ["number", "name", "sessionTitle", "speaker", "schedule"]:
            sort_by = "number"

        super(AbstractBook, self).__init__(conf, aw, None, tz, sort_by)

        del self._args["url"]


class TimetablePDFFormat:

    def __init__(self, params=None):
        if params is None:
            self.contribId = True
            self.speakerTitle = True
            self.contribAbstract = False
            self.newPagePerSession = False
            self.useSessionColorCodes = False
            self.showSessionTOC = False
            self.logo = False
            self.lengthContribs = False
            self.contribsAtConfLevel=False
            self.breaksAtConfLevel=False
            self.dateCloseToSessions=False
            self.coverPage=True
            self.tableContents=True
        else:
            self.setValues(params)

    def setValues(self, params):
        self.contribId = True
        if not params.has_key("showContribId"):
            self.contribId = False

        self.speakerTitle = True
        if not params.has_key("showSpeakerTitle"):
            self.speakerTitle = False

        self.contribAbstract = False
        if params.has_key("showAbstract"):
            self.contribAbstract = True

        self.contribPosterAbstract = True
        if params.has_key("dontShowPosterAbstract"):
            self.contribPosterAbstract = False

        self.newPagePerSession = False
        if params.has_key("newPagePerSession"):
            self.newPagePerSession = True

        self.useSessionColorCodes = False
        if params.has_key("useSessionColorCodes"):
            self.useSessionColorCodes = True

        self.showSessionTOC = False
        if params.has_key("showSessionTOC"):
            self.showSessionTOC = True

        self.lengthContribs = False
        if params.has_key("showLengthContribs"):
            self.lengthContribs = True

        self.contribsAtConfLevel = False
        if params.has_key("showContribsAtConfLevel"):
            self.contribsAtConfLevel = True

        self.breaksAtConfLevel = False
        if params.has_key("showBreaksAtConfLevel"):
            self.breaksAtConfLevel = True

        self.dateCloseToSessions = False
        if params.has_key("printDateCloseToSessions"):
            self.dateCloseToSessions = True

        self.coverPage=True
        if not params.has_key("showCoverPage"):
            self.coverPage = False

        self.tableContents=True
        if not params.has_key("showTableContents"):
            self.tableContents = False

        self.logo = False

    def showContribId(self):
        return self.contribId

    def showSpeakerTitle(self):
        return self.speakerTitle

    def showContribAbstract(self):
        return self.contribAbstract

    def showContribPosterAbstract(self):
        return self.contribPosterAbstract

    def showLogo(self):
        return self.logo

    def showNewPagePerSession(self):
        return self.newPagePerSession

    def showUseSessionColorCodes(self):
        return self.useSessionColorCodes

    def showTitleSessionTOC(self):
        return self.showSessionTOC

    def showLengthContribs(self):
        return self.lengthContribs

    def showContribsAtConfLevel(self):
        return self.contribsAtConfLevel

    def showBreaksAtConfLevel(self):
        return self.breaksAtConfLevel

    def showDateCloseToSessions(self):
        return self.dateCloseToSessions

    def showCoverPage(self):
        return self.coverPage

    def showTableContents(self):
        return self.tableContents


def sortEntries(x,y):
    if cmp(x.getStartDate(), y.getStartDate()):
        return cmp(x.getStartDate(), y.getStartDate())
    elif isinstance(x.getOwner(), conference.SessionSlot) and \
            isinstance(y.getOwner(), conference.SessionSlot):
        val = cmp(x.getOwner().getSession().getCode(), y.getOwner().getSession().getCode())

        if val:
            return val
        else:
            return cmp(x.getOwner().getSession().getTitle(), y.getOwner().getSession().getTitle())
    else:
        return cmp(x.getTitle(), y.getTitle())


class TimeTablePlain(PDFWithTOC):
    def __init__(self, conf, aw, showSessions=None, showDays=None, sortingCrit=None, ttPDFFormat=None,
                 pagesize='A4', fontsize='normal', firstPageNumber=1, showSpeakerAffiliation=False, tz=None):
        self._conf = conf
        self._event = conf.as_event
        self._aw = aw
        self._tz = DisplayTZ(self._aw, self._conf).getDisplayTZ()
        self._showSessions = showSessions
        self._showDays = showDays
        self._ttPDFFormat = ttPDFFormat or TimetablePDFFormat()
        story = None if self._ttPDFFormat.showCoverPage() else []
        PDFWithTOC.__init__(self, story=story, pagesize=pagesize, fontsize=fontsize, firstPageNumber=firstPageNumber)
        self._title = _("Programme")
        self._doc.leftMargin = 1 * cm
        self._doc.rightMargin = 1 * cm
        self._doc.topMargin = 1.5 * cm
        self._doc.bottomMargin = 1 * cm
        self._sortingCrit = sortingCrit
        self._firstPageNumber = firstPageNumber
        self._showSpeakerAffiliation = showSpeakerAffiliation

    def _processTOCPage(self):
        if self._ttPDFFormat.showTableContents():
            style1 = ParagraphStyle({})
            style1.fontName = "Times-Bold"
            style1.fontSize = modifiedFontSize(18, self._fontsize)
            style1.leading = modifiedFontSize(22, self._fontsize)
            style1.alignment = TA_CENTER
            self._story.append(Spacer(inch, 1 * cm))
            self._story.append(Paragraph(_("Table of contents"), style1))
            self._story.append(Spacer(inch, 1 * cm))
            if self._showSessions:
                style2 = ParagraphStyle({})
                style2.fontSize = modifiedFontSize(14, self._fontsize)
                style2.leading = modifiedFontSize(10, self._fontsize)
                style2.alignment = TA_CENTER
                sess_captions = [sess.title for sess in self._event.sessions if sess.id in self._showSessions]
                p = Paragraph("\n".join(sess_captions), style2)
                self._story.append(p)
            self._story.append(Spacer(inch, 2 * cm))
            self._story.append(self._toc)
            self._story.append(PageBreak())

    def firstPage(self, c, doc):
        if self._ttPDFFormat.showCoverPage():
            c.saveState()
            if self._ttPDFFormat.showLogo():
                self._drawLogo(c, False)

            height = self._drawWrappedString(c, self._event.title)
            c.setFont('Times-Bold', modifiedFontSize(15, self._fontsize))
            height -= 2 * cm
            c.drawCentredString(self._PAGE_WIDTH / 2.0, height,
                                "{} - {}".format(format_date(self._event.start_dt, format='full', timezone=self._tz),
                                                 format_date(self._event.end_dt, format='full', timezone=self._tz)))
            if self._event.venue_name:
                height -= 2 * cm
                c.drawCentredString(self._PAGE_WIDTH / 2.0, height, escape(self._event.venue_name))
            c.setFont('Times-Bold', modifiedFontSize(30, self._fontsize))
            height -= 1 * cm
            c.drawCentredString(self._PAGE_WIDTH / 2.0, height, self._title)
            self._drawWrappedString(c, "{} / {}".format(self._event.title, self._title), width=inch,
                                    height=0.75 * inch, font='Times-Roman', size=modifiedFontSize(9, self._fontsize),
                                    color=(0.5, 0.5, 0.5), align="left", maximumWidth=self._PAGE_WIDTH - 3.5 * inch,
                                    measurement=inch, lineSpacing=0.15)
            c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, nowutc().strftime("%A %d %B %Y"))
            c.restoreState()

    def laterPages(self, c, doc):
        c.saveState()
        maxi = self._PAGE_WIDTH - 2 * cm
        if doc.getCurrentPart().strip():
            maxi = self._PAGE_WIDTH - 6 * cm
        self._drawWrappedString(c, "{} / {}".format(self._event.title, self._title), width=1 * cm,
                                height=self._PAGE_HEIGHT - 1 * cm, font='Times-Roman',
                                size=modifiedFontSize(9, self._fontsize), color=(0.5, 0.5, 0.5), align="left",
                                lineSpacing=0.3, maximumWidth=maxi)
        c.drawCentredString(self._PAGE_WIDTH / 2.0, 0.5 * cm,
                            i18nformat(""" _("Page") {} """).format(doc.page + self._firstPageNumber - 1))
        c.drawRightString(self._PAGE_WIDTH - 1 * cm, self._PAGE_HEIGHT - 1 * cm, doc.getCurrentPart())
        c.restoreState()

    def _defineStyles(self):
        self._styles = {}

        stylesheet = getSampleStyleSheet()
        dayStyle = stylesheet["Heading1"]
        dayStyle.fontSize = modifiedFontSize(dayStyle.fontSize, self._fontsize)
        self._styles["day"] = dayStyle

        sessionTitleStyle = stylesheet["Heading2"]
        sessionTitleStyle.fontSize = modifiedFontSize(12.0, self._fontsize)
        self._styles["session_title"] = sessionTitleStyle

        sessionDescriptionStyle = stylesheet["Heading2"]
        sessionDescriptionStyle.fontSize = modifiedFontSize(10.0, self._fontsize)
        self._styles["session_description"] = sessionDescriptionStyle

        self._styles["table_body"] = stylesheet["Normal"]

        convenersStyle = stylesheet["Normal"]
        convenersStyle.fontSize = modifiedFontSize(10.0, self._fontsize)
        convenersStyle.leftIndent = 10
        self._styles["conveners"] = convenersStyle

        subContStyle = stylesheet["Normal"]
        subContStyle.fontSize = modifiedFontSize(10.0, self._fontsize)
        subContStyle.leftIndent = 15
        self._styles["subContrib"] = subContStyle

    def _getSessionColor(self, block):
        session_color = '#{}'.format(block.session.colors.background)
        return html_color_to_rgb(session_color)

    def _get_speaker_name(self, speaker):
        speaker_name = speaker.get_full_name(last_name_first=False, show_title=self._ttPDFFormat.showSpeakerTitle())
        if self._showSpeakerAffiliation and speaker.affiliation:
            speaker_name += " ({})".format(speaker.affiliation)
        return speaker_name

    def _processContribution(self, contrib, l):
        if not contrib.can_access(self._aw):
            return

        lt = []
        date = Paragraph(format_time(contrib.start_dt, timezone=self._tz), self._styles["table_body"])
        caption = '[{}] {}'.format(contrib.id, escape(contrib.title))

        if not self._ttPDFFormat.showContribId():
            caption = escape(contrib.title)
        elif self._ttPDFFormat.showLengthContribs():
            caption = "{} ({})".format(caption, format_human_timedelta(contrib.timetable_entry.duration))
        elif self._ttPDFFormat.showContribAbstract():
            caption = '<font face="Times-Bold"><b>{}</b></font>'.format(caption)

        color_cell = ""
        caption = '<font size="{}">{}</font>'.format(str(modifiedFontSize(10, self._fontsize)), caption)
        lt.append([self._fontify(caption, 10)])

        if self._useColors():
            color_cell = " "
        if self._ttPDFFormat.showContribAbstract():
            speaker_list = [self._get_speaker_name(spk) for spk in contrib.speakers]
            if speaker_list:
                if len(speaker_list) == 1:
                    speaker_title = i18nformat(""" _("Presenter"): """)
                else:
                    speaker_title = i18nformat(""" _("Presenters"): """)
                speaker_content = speaker_title + ", ".join(speaker_list)
                speaker_content = '<font name="Times-Italic"><i>{}</i></font>'.format(speaker_content)
                lt.append([self._fontify(speaker_content, 9)])
            caption = escape(contrib.description)
            lt.append([self._fontify(caption, 9)])
            caption_and_speakers = Table(lt, colWidths=None, style=self._tsSpk)
            if color_cell:
                l.append([color_cell, date, caption_and_speakers])
            else:
                l.append([date, caption_and_speakers])
        else:
            caption = Table(lt, colWidths=None, style=self._tsSpk)
            speaker_list = [[Paragraph(escape(self._get_speaker_name(spk)), self._styles["table_body"])]
                            for spk in contrib.speakers]
            if not speaker_list:
                speaker_list = [[""]]
            speakers = Table(speaker_list, style=self._tsSpk)
            if color_cell:
                l.append([color_cell, date, caption, speakers])
            else:
                l.append([date, caption, speakers])

        for subc in contrib.subcontributions:
            if not subc.can_access(self._aw):
                return

            lt = []
            caption = '- [{}] {}'.format(subc.id, escape(subc.title))
            if not self._ttPDFFormat.showContribId():
                caption = '- {}' .format(escape(subc.title))
            elif self._ttPDFFormat.showLengthContribs():
                caption = '{} ({})'.format(caption, format_human_timedelta(subc.timetable_entry.duration))

            caption = '<font size="{}">{}</font>'.format(str(modifiedFontSize(10, self._fontsize)), caption)
            lt.append([Paragraph(caption, self._styles["subContrib"])])
            if self._ttPDFFormat.showContribAbstract():
                caption = '<font size="{}">{}</font>'.format(str(modifiedFontSize(9, self._fontsize)),
                                                             escape(subc.description))
                lt.append([Paragraph(caption, self._styles["subContrib"])])

            speaker_list = [[Paragraph(escape(self._get_speaker_name(spk)), self._styles["table_body"])]
                            for spk in subc.speakers]
            if not speaker_list:
                speaker_list = [[""]]
            if self._ttPDFFormat.showContribAbstract():
                lt.extend(speaker_list)
                caption_and_speakers = Table(lt, colWidths=None, style=self._tsSpk)
                if color_cell:
                    l.append([color_cell, "", caption_and_speakers])
                else:
                    l.append(["", caption_and_speakers])
            else:
                caption = Table(lt, colWidths=None, style=self._tsSpk)
                speakers = Table(speaker_list, style=self._tsSpk)
                if color_cell:
                    l.append([color_cell, "", caption, speakers])
                else:
                    l.append(["", caption, speakers])

    def _processPosterContribution(self, contrib, l):
        if not contrib.can_access(self._aw):
            return

        lt = []
        caption_text = "[{}] {}".format(contrib.id, escape(contrib.title))
        if not self._ttPDFFormat.showContribId():
            caption_text = escape(contrib.title)
        if self._ttPDFFormat.showLengthContribs():
            caption_text = "{} ({})".format(caption_text, format_human_timedelta(contrib.duration))
        caption_text = '<font name="Times-Bold">{}</font>'.format(caption_text)
        lt.append([self._fontify(caption_text, 10)])
        board_number = contrib.board_number
        if self._ttPDFFormat.showContribAbstract() and self._ttPDFFormat.showContribPosterAbstract():
            speaker_list = [self._get_speaker_name(spk) for spk in contrib.speakers]
            if speaker_list:
                if len(speaker_list) == 1:
                    speaker_word = i18nformat('_("Presenter"): ')
                else:
                    speaker_word = i18nformat('_("Presenters"): ')
                speaker_text = speaker_word + ", ".join(speaker_list)
                speaker_text = '<font face="Times-Italic"><i>{}</i></font>'.format(speaker_text)
                lt.append([self._fontify(speaker_text, 10)])
            caption_text = escape(contrib.description)
            lt.append([self._fontify(caption_text, 9)])
            caption_and_speakers = Table(lt, colWidths=None, style=self._tsSpk)
            if self._useColors():
                l.append([" ", caption_and_speakers, board_number])
            else:
                l.append([caption_and_speakers, board_number])
        else:
            caption = Table(lt, colWidths=None, style=self._tsSpk)
            speaker_list = [[Paragraph(escape(self._get_speaker_name(spk)), self._styles["table_body"])]
                            for spk in contrib.speakers]
            if not speaker_list:
                speaker_list = [[""]]
            speakers = Table(speaker_list, style=self._tsSpk)
            if self._useColors():
                l.append([" ", caption, speakers, board_number])
            else:
                l.append([caption, speakers, board_number])
        for subc in contrib.subcontributions:
            if not subc.can_access(self._aw):
                return

            lt = []
            caption_text = "- [{}] {}".format(subc.id, escape(subc.title))
            if not self._ttPDFFormat.showContribId():
                caption_text = "- {}".format(subc.id)
            if self._ttPDFFormat.showLengthContribs():
                caption_text = "{} ({})".format(caption_text, escape(format_human_timedelta(subc.duration)))
            lt.append([Paragraph(caption_text, self._styles["subContrib"])])
            if self._ttPDFFormat.showContribAbstract():
                caption_text = '<font size="{}">{}</font>'.format(str(modifiedFontSize(9, self._fontsize)),
                                                                  escape(subc.description))
                lt.append([Paragraph(caption_text, self._styles["subContrib"])])
            speaker_list = [[Paragraph(escape(self._get_speaker_name(spk)), self._styles["table_body"])]
                            for spk in subc.speakers]
            caption = Table(lt, colWidths=None, style=self._tsSpk)
            if not speaker_list:
                speaker_list = [[""]]
            speakers = Table(speaker_list, style=self._tsSpk)
            l.append(["", caption, speakers])

    def _getNameWithoutTitle(self, av):
        return av.full_name

    def _useColors(self):
        return self._ttPDFFormat.showUseSessionColorCodes()

    def _fontify(self, text, fSize=10, fName=""):
        style = getSampleStyleSheet()["Normal"]
        style.fontSize = modifiedFontSize(fSize, self._fontsize)
        style.leading = modifiedFontSize(fSize + 3, self._fontsize)
        return Paragraph(text, style)

    def _fontifyRow(self, row, fSize=10, fName=""):
        return [self._fontify(text, fSize, fName) for text in row]

    def _processDayEntries(self, day, story):
        res = []
        originalts = TableStyle([('VALIGN', (0, 0), (-1, -1), "TOP"),
                                 ('LEFTPADDING', (0, 0), (-1, -1), 1),
                                 ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                                 ('GRID', (0, 1), (-1, -1), 1, colors.lightgrey)])
        self._tsSpk = TableStyle([("LEFTPADDING", (0, 0), (0, -1), 0),
                                  ("RIGHTPADDING", (0, 0), (0, -1), 0),
                                  ("TOPPADDING", (0, 0), (0, -1), 1),
                                  ("BOTTOMPADDING", (0, 0), (0, -1), 0)])
        colorts = TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 3),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("TOPPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                              ('GRID', (0, 0), (0, -1), 1, colors.lightgrey)])
        entries = (self._conf.as_event.timetable_entries
                   .filter(cast(TimetableEntry.start_dt, Date) == day.date(), TimetableEntry.parent_id.is_(None))
                   .order_by(TimetableEntry.start_dt))
        for entry in entries:
            # Session slot
            if entry.type == TimetableEntryType.SESSION_BLOCK:
                sess_block = entry.object
                if self._showSessions and sess_block.session.id not in self._showSessions:
                    continue
                if not sess_block.can_access(self._aw):
                    continue

                room = ''
                if sess_block.room_name:
                    room = ' - {}'.format(escape(sess_block.room_name))

                session_caption = escape(sess_block.full_title)
                conv = []
                for c in sess_block.person_links:
                    if self._showSpeakerAffiliation and c.affiliation:
                        conv.append("{} ({})".format(escape(c.full_name), escape(c.affiliation)))
                    else:
                        conv.append(escape(c.full_name))

                conv = '; '.join(conv)
                if conv:
                    conv = i18nformat('<font face="Times-Bold"><b>-_("Conveners"): {}</b></font>').format(conv)

                res.append(Paragraph('', self._styles["session_title"]))
                start_dt = format_time(sess_block.timetable_entry.start_dt, timezone=self._tz)

                if self._ttPDFFormat.showDateCloseToSessions():
                    start_dt = format_datetime(sess_block.timetable_entry.start_dt, timezone=self._tz)

                sess_caption = '<font face="Times-Bold">{}</font>'.format(escape(session_caption))
                text = '<u>{}</u>{} ({}-{})'.format(sess_caption, room, start_dt,
                                                    format_time(sess_block.timetable_entry.end_dt, timezone=self._tz))

                p1 = Paragraph(text, self._styles["session_title"])
                if self._useColors():
                    ts = deepcopy(colorts)
                    ts.add('BACKGROUND', (0, 0), (0, -1), self._getSessionColor(sess_block))
                    p1 = Table([["", p1]], colWidths=[0.2 * cm, None], style=ts)

                res.append(p1)
                if self._ttPDFFormat.showTitleSessionTOC():
                    self._indexedFlowable[p1] = {'text': escape(sess_block.session.title), 'level': 2}

                # add session description
                if sess_block.session.description:
                    text = '<i>{}</i>'.format(escape(sess_block.session.description))
                    res.append(Paragraph(text, self._styles["session_description"]))

                p2 = Paragraph(conv, self._styles["conveners"])
                res.append(p2)
                l = []
                ts = deepcopy(originalts)
                contribs = sorted(sess_block.contributions, key=attrgetter('timetable_entry.start_dt'))
                if sess_block.session.is_poster:
                    for contrib in contribs:
                        self._processPosterContribution(contrib, l)

                    if l:
                        title = "[id] title"
                        if not self._ttPDFFormat.showContribId():
                            title = "title"
                        if self._ttPDFFormat.showContribAbstract() and self._ttPDFFormat.showContribPosterAbstract():
                            # presenter integrated in 1st column -> 2 columns only
                            row = [title, "board"]
                            widths = [None, 1 * cm]
                        else:
                            row = [title, "presenter", "board"]
                            widths = [None, 5 * cm, 1 * cm]
                        row = self._fontifyRow(row, 11)
                        if self._useColors():
                            row.insert(0, "")
                            widths.insert(0, 0.2 * cm)
                        l.insert(0, row)
                        if self._useColors():
                            ts.add('BACKGROUND', (0, 1), (0, -1), self._getSessionColor(sess_block))
                        t = Table(l, colWidths=widths, style=ts)
                else:  # it's not a poster
                    for s_entry in sorted(sess_block.timetable_entry.children, key=attrgetter('start_dt')):
                        obj = s_entry.object
                        if s_entry.type == TimetableEntryType.CONTRIBUTION:
                            self._processContribution(obj, l)
                        elif s_entry.type == TimetableEntryType.BREAK:
                            lt = []
                            date = self._fontify('{}'.format(format_time(s_entry.start_dt, timezone=self._tz)))
                            caption = obj.title

                            if self._ttPDFFormat.showLengthContribs():
                                caption = '{} ({})'.format(caption, format_human_timedelta(s_entry.duration))

                            lt.append([self._fontify(caption, 10)])
                            caption = Table(lt, colWidths=None, style=self._tsSpk)

                            if self._ttPDFFormat.showContribAbstract():
                                row = [date, caption]
                            else:
                                row = [date, caption, ""]
                            if self._useColors():
                                row.insert(0, "")
                            l.append(row)
                    if l:
                        title = "[id] title"
                        if not self._ttPDFFormat.showContribId():
                            title = "title"
                        if self._ttPDFFormat.showContribAbstract():
                            # presenter integrated in 1st column -> 2 columns only
                            row = ["time", title]
                            widths = [1 * cm, None]
                        else:
                            row = ["time", title, "presenter"]
                            widths = [1 * cm, None, 5 * cm]
                        row = self._fontifyRow(row, 11)
                        if self._useColors():
                            row.insert(0, "")
                            widths.insert(0, 0.2 * cm)
                        l.insert(0, row)
                        if self._useColors():
                            ts.add('BACKGROUND', (0, 1), (0, -1), self._getSessionColor(sess_block))
                        t = Table(l, colWidths=widths, style=ts)

                if l:
                    res.append(t)
                    if self._ttPDFFormat.showNewPagePerSession():
                        res.append(PageBreak())
                elif entry == entries[-1]:  # if it is the last one, we do the page break and remove the previous one.
                    res = list(takewhile(lambda x: not isinstance(x, PageBreak)), res)
                    if self._ttPDFFormat.showNewPagePerSession():
                        res.append(PageBreak())
            # contribution
            elif self._ttPDFFormat.showContribsAtConfLevel() and entry.type == TimetableEntryType.CONTRIBUTION:
                contrib = entry.object
                if not contrib.can_access(self._aw):
                    continue

                room = ''
                if contrib.room_name:
                    room = ' - {}'.format(escape(contrib.room_name))

                speakers = ';'.join([self._get_speaker_name(spk) for spk in contrib.speakers])
                if speakers.strip():
                    speakers = i18nformat('<font face="Times-Bold"><b>-_("Presenters"): {}</b></font>').format(speakers)

                text = '<u>{}</u>{} ({}-{})'.format(escape(contrib.title), room,
                                                    format_time(entry.start_dt, timezone=self._tz),
                                                    format_time(entry.end_dt, timezone=self._tz))
                p1 = Paragraph(text, self._styles["session_title"])
                res.append(p1)
                if self._ttPDFFormat.showTitleSessionTOC():
                    self._indexedFlowable[p1] = {'text': escape(contrib.title), 'level': 2}

                p2 = Paragraph(speakers, self._styles["conveners"])
                res.append(p2)
                if entry == entries[-1]:  # if it is the last one, we do the page break and remove the previous one.
                    res = list(takewhile(lambda x: not isinstance(x, PageBreak)), res)
                    if self._ttPDFFormat.showNewPagePerSession():
                        res.append(PageBreak())
            # break
            elif self._ttPDFFormat.showBreaksAtConfLevel() and entry.type == TimetableEntryType.BREAK:
                break_entry = entry
                break_ = break_entry.object
                room = ''
                if break_.room_name:
                    room = ' - {}'.format(escape(break_.room_name))

                text = '<u>{}</u>{} ({}-{})'.format(escape(break_.title), room,
                                                    format_time(break_entry.start_dt, timezone=self._tz),
                                                    format_time(break_entry.end_dt, timezone=self._tz))

                p1 = Paragraph(text, self._styles["session_title"])
                res.append(p1)

                if self._ttPDFFormat.showTitleSessionTOC():
                    self._indexedFlowable[p1] = {'text': escape(break_.title), 'level': 2}

                if entry == entries[-1]:  # if it is the last one, we do the page break and remove the previous one.
                    res = list(takewhile(lambda x: not isinstance(x, PageBreak)), res)
                    if self._ttPDFFormat.showNewPagePerSession():
                        res.append(PageBreak())
        return res

    def getBody(self, story=None):
        self._defineStyles()
        if not story:
            story = self._story
        if not self._ttPDFFormat.showCoverPage():
            s = ParagraphStyle({})
            s.fontName = "Times-Bold"
            s.fontSize = 18
            s.leading = 22
            s.alignment = TA_CENTER
            p = Paragraph(escape(self._conf.getTitle()), s)
            story.append(p)
            story.append(Spacer(1, 0.4 * inch))

        current_day = self._event.start_dt
        while current_day <= self._event.end_dt:
            if self._showDays and current_day.strftime("%d-%B-%Y") not in self._showDays:
                current_day += timedelta(days=1)
                continue

            day_entries = self._processDayEntries(current_day, story)
            if not day_entries:
                current_day += timedelta(days=1)
                continue

            text = escape(current_day.strftime("%A %d %B %Y"))
            p = Paragraph(text, self._styles["day"], part=current_day.strftime("%A %d %B %Y"))
            story.append(p)
            self._indexedFlowable[p] = {"text": current_day.strftime("%A %d %B %Y"), "level": 1}
            for entry in day_entries:
                story.append(entry)
            if not self._ttPDFFormat.showNewPagePerSession():
                story.append(PageBreak())
            current_day += timedelta(days=1)


class SimplifiedTimeTablePlain(PDFBase):
    def __init__(self, conf, aw, showSessions=[], showDays=[], sortingCrit=None, ttPDFFormat=None, pagesize='A4',
                 fontsize='normal', tz=None):
        self._conf = conf
        self._event = conf.as_event
        self._tz = tz or self._conf.getTimezone()
        self._aw = aw
        self._showSessions = showSessions
        self._showDays = showDays
        PDFBase.__init__(self, story=[], pagesize=pagesize)
        self._title = _("Simplified Programme")
        self._doc.leftMargin = 1 * cm
        self._doc.rightMargin = 1 * cm
        self._doc.topMargin = 1 * cm
        self._doc.bottomMargin = 1 * cm
        self._sortingCrit = sortingCrit
        self._ttPDFFormat = ttPDFFormat or TimetablePDFFormat()
        self._fontsize = fontsize

    def _defineStyles(self):
        self._styles = {}
        stylesheets = getSampleStyleSheet()

        normalStl = stylesheets["Normal"]
        normalStl.fontName = "Courier"
        normalStl.fontSize = modifiedFontSize(10, self._fontsize)
        normalStl.spaceBefore = 0
        normalStl.spaceAfter = 0
        normalStl.alignment = TA_LEFT
        self._styles["normal"] = normalStl
        titleStl = stylesheets["Normal"]
        titleStl.fontName = "Courier-Bold"
        titleStl.fontSize = modifiedFontSize(12, self._fontsize)
        titleStl.spaceBefore = 0
        titleStl.spaceAfter = 0
        titleStl.alignment = TA_LEFT
        self._styles["title"] = titleStl
        dayStl = stylesheets["Normal"]
        dayStl.fontName = "Courier-Bold"
        dayStl.fontSize = modifiedFontSize(10, self._fontsize)
        dayStl.spaceBefore = 0
        dayStl.spaceAfter = 0
        dayStl.alignment = TA_LEFT
        self._styles["day"] = dayStl

    def _haveSessionSlotsTitles(self, session):
        """Checks if the session has slots with titles or not"""
        for ss in session.blocks:
            if ss.title.strip():
                return True
        return False

    def _processDayEntries(self, day, story):
        lastSessions = []  # this is to avoid checking if the slots have titles for all the slots
        res = []
        entries = (self._event.timetable_entries
                   .filter(cast(TimetableEntry.start_dt) == day.date(),
                           TimetableEntry.parent_id.is_(None))
                   .order_by(TimetableEntry.start_dt))
        for entry in entries:
            if entry.type == TimetableEntryType.SESSION_BLOCK:
                session_slot = entry.object
                sess = session_slot.session
                if self._showSessions and sess.id not in self._showSessions:
                    continue
                if not session_slot.can_access(self._aw):
                    continue
                if sess in lastSessions:
                    continue
                if self._haveSessionSlotsTitles(sess):
                    e = session_slot
                else:
                    lastSessions.append(sess)
                    e = sess
                title = e.title
                res.append(Paragraph(i18nformat('<font face="Times-Bold"><b> _("Session"):</b></font> {}')
                                     .format(escape(title)), self._styles["normal"]))
                room_time = ""
                if session_slot.room_name:
                    room_time = escape(session_slot.room_name)
                room_time = (i18nformat('<font face="Times-Bold"><b> _("Time and Place"):</b></font> {}({}-{})')
                             .format(room_time, format_date(entry.start_dt, timezone=self._tz),
                                     format_date(entry.end_dt, timezone=self._tz)))
                res.append(Paragraph(room_time, self._styles["normal"]))
                chairs = []
                for c in session_slot.person_links:
                    chairs.append(c.full_name)

                if chairs:
                    res.append(Paragraph(i18nformat('<font face="Times-Bold"><b> _("Chair/s"):</b></font> {}')
                                         .format("; ".join(chairs)), self._styles["normal"]))
                res.append(Spacer(1, 0.2 * inch))
            elif self._ttPDFFormat.showContribsAtConfLevel() and entry.type == TimetableEntryType.CONTRIBUTION:
                contrib = entry.object
                if not contrib.can_access(self._aw):
                    continue

                title = contrib.title
                res.append(Paragraph(i18nformat('<font face="Times-Bold"><b> _("Contribution"):</b></font> {}')
                                     .format(escape(title)), self._styles["normal"]))
                room_time = ""
                if contrib.room_name:
                    room_time = escape(contrib.room_name)

                room_time = (i18nformat('<font face="Times-Bold"><b> _("Time and Place"):</b></font> {}({}-{})')
                             .format(room_time, format_date(entry.start_dt, timezone=self._tz),
                                     format_date(entry.end_dt, timezone=self._tz)))
                res.append(Paragraph(room_time, self._styles["normal"]))
                spks = []
                for c in contrib.speakers:
                    spks.append(c.full_name)
                if spks:
                    res.append(Paragraph(i18nformat('<font face="Times-Bold"><b> _("Presenter/s"):</b></font> {}')
                                         .format("; ".join(spks)), self._styles["normal"]))
                res.append(Spacer(1, 0.2 * inch))
            elif self._ttPDFFormat.showBreaksAtConfLevel() and entry.type == TimetableEntryType.BREAK:
                break_ = entry.object
                title = break_.title
                res.append(Paragraph(i18nformat('<font face="Times-Bold"><b> _("Break"):</b></font> {}')
                                     .format(escape(title)), self._styles["normal"]))
                room_time = ""
                if break_.room_name:
                    room_time = escape(break_.room_name)
                room_time = (i18nformat('<font face="Times-Bold"><b> _("Time and Place"):</b></font> {}({}-{})')
                             .format(room_time, format_date(entry.start_dt, timezone=self._tz),
                                     format_date(entry.end_dt, timezone=self._tz)))
                res.append(Paragraph(room_time, self._styles["normal"]))
                res.append(Spacer(1, 0.2 * inch))
        res.append(PageBreak())
        return res

    def getBody(self, story=None):
        self._defineStyles()
        if not story:
            story = self._story

        currentDay = self._event.start_dt
        while currentDay <= self._event.end_dt:
            if len(self._showDays) > 0 and currentDay.strftime("%d-%B-%Y") not in self._showDays:
                currentDay += timedelta(days=1)
                continue

            dayEntries = self._processDayEntries(currentDay, story)
            if not dayEntries:
                currentDay += timedelta(days=1)
                continue
            if self._event.end_dt.astimezone(timezone(self._tz)).month != self._conf.getAdjustedEndDate(self._tz).month:
                text = "%s - %s-%s" % (escape(self._event.title), escape(format_date(self._event.start_dt,
                                                                                     timezone=self._tz)),
                                       escape(format_date(self._event.end_dt, timezone=self._tz)))
            else:
                text = "%s - %s-%s" % (escape(self._event.title),
                                       escape(format_date(self._event.start_dt, format='dd', timezone=self._tz)),
                                       escape(format_date(self._event.end_dt, format='dd MM YY', timezone=self._tz)))
            if self._event.venue_name:
                text = "%s, %s." % (text, self._event.venue_name)
            text = "%s" % text
            p = Paragraph(text, self._styles["title"])
            story.append(p)
            text2 = i18nformat(""" _("Daily Programme"): %s""") % escape(currentDay.strftime("%A %d %B %Y"))
            p2 = Paragraph(text2, self._styles["day"])
            story.append(p2)
            story.append(Spacer(1, 0.4 * inch))
            for entry in dayEntries:
                story.append(entry)
            currentDay += timedelta(days=1)


class FilterCriteria(filters.FilterCriteria):
    _availableFields = {
        contribFilters.StatusFilterField.getId():contribFilters.StatusFilterField
                }


class RegistrantToPDF(PDFBase):

    def __init__(self, conf, reg, display, doc=None, story=None, special_items=None):
        self._reg = reg
        self._conf = conf
        self._display = display
        self.special_items = special_items
        if not story:
            story = [Spacer(inch, 5*cm)]
        PDFBase.__init__(self, doc, story)
        self._title = _("Registrant")
        self._PAGE_HEIGHT = defaultPageSize[1]
        self._PAGE_WIDTH = defaultPageSize[0]

    def firstPage(self, c, doc):
        c.saveState()
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 25)
        #c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT - inch - 5*cm, self._abstract.getTitle())
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        #c.line(inch, self._PAGE_HEIGHT - inch - 6*cm, self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - inch - 6*cm)
        #c.line(inch, inch , self._PAGE_WIDTH - inch, inch)
        c.setFont('Times-Roman', 10)
        #c.drawString(0.5*inch, 0.5*inch, Config.getInstance().getBaseURL())
        c.restoreState()

    def getBody(self, story=None, indexedFlowable=None, level=1 ):
        if not story:
            story = self._story
        style = ParagraphStyle({})
        style.fontSize = 12

        registration = self._reg
        data = registration.data_by_field
        full_name = "{first_name} {last_name}".format(first_name=registration.first_name.encode('utf-8'),
                                                      last_name=registration.last_name.encode('utf-8'))

        def _append_text_to_story(text, space=0.2, indexed_flowable=False):
            p = Paragraph(text, style, full_name)
            if indexed_flowable:
                indexedFlowable[p] = {"text": full_name, "level": 1}
            story.append(p)
            story.append(Spacer(inch, space*cm, full_name))

        def _print_row(caption, value):
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            text = '<b>{field_name}</b>: {field_value}'.format(field_name=caption.encode('utf-8'), field_value=value)
            _append_text_to_story(text)

        text = _('Registrant ID: {id}').format(id=registration.friendly_id)
        _append_text_to_story(text, space=0.5)

        style = ParagraphStyle({})
        style.alignment = TA_CENTER
        style.fontSize = 25
        style.leading = 30
        _append_text_to_story(full_name, space=1.0, indexed_flowable=True)
        style = ParagraphStyle({})
        style.alignment = TA_JUSTIFY

        for item in self._display:
            if item.input_type == 'accommodation' and item.id in data:
                _print_row(caption=item.title, value=data[item.id].friendly_data.get('choice'))
                arrival_date = data[item.id].friendly_data.get('arrival_date')
                _print_row(caption=_('Arrival date'), value=format_date(arrival_date) if arrival_date else '')
                departure_date = data[item.id].friendly_data.get('departure_date')
                _print_row(caption=_('Departure date'), value=format_date(departure_date) if departure_date else '')
            elif item.input_type == 'multi_choice' and item.id in data:
                multi_choice_data = ', '.join(data[item.id].friendly_data)
                _print_row(caption=item.title, value=multi_choice_data)
            else:
                value = data[item.id].friendly_data if item.id in data else ''
                _print_row(caption=item.title, value=value)

        if 'reg_date' in self.special_items:
            _print_row(caption=_('Registration date'), value=format_datetime(registration.submitted_dt))
        if 'state' in self.special_items:
            _print_row(caption=_('Registration state'), value=registration.state.title)
        if 'price' in self.special_items:
            _print_row(caption=_('Price'), value=registration.render_price())
        if 'checked_in' in self.special_items:
            checked_in = 'Yes' if registration.checked_in else 'No'
            _print_row(caption=_('Checked in'), value=checked_in)
        if 'checked_in_date' in self.special_items:
            check_in_date = format_datetime(registration.checked_in_dt) if registration.checked_in else ''
            _print_row(caption=_('Check-in date'), value=check_in_date)

        return story


class RegistrantsListToBookPDF(PDFWithTOC):
    def __init__(self, conf, doc=None, story=[], reglist=None, display=[], special_items=None):
        self._conf = conf
        self._regList = reglist
        self._display = display
        self._title = _("Registrants Book")
        self.special_items = special_items
        PDFWithTOC.__init__(self)

    def firstPage(self, c, doc):
        c.saveState()
        showLogo = False
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 35)
        c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT/2, self._title)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        #c.line(inch, self._PAGE_HEIGHT - inch - 6*cm, self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - inch - 6*cm)
        #c.line(inch, inch , self._PAGE_WIDTH - inch, inch)
        c.setFont('Times-Roman', 10)
        c.drawString(0.5*inch, 0.5*inch, str(urlHandlers.UHConferenceDisplay.getURL(self._conf)))
        c.restoreState()

    def laterPages(self, c, doc):

        c.saveState()
        c.setFont('Times-Roman', 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        confTitle = escape(self._conf.getTitle())
        if len(self._conf.getTitle())>30:
            confTitle = escape(self._conf.getTitle()[:30] + "...")
        c.drawString(inch, self._PAGE_HEIGHT - 0.75 * inch, "%s / %s"%(confTitle, self._title))
        title = doc.getCurrentPart()
        if len(doc.getCurrentPart())>50:
            title = utils.unicodeSlice(doc.getCurrentPart(), 0, 50) + "..."
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, "%s"%title)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, i18nformat(""" _("Page") %d """)%doc.page)
        c.drawString(inch,  0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()

    def getBody(self):
        for reg in self._regList:
            temp = RegistrantToPDF(self._conf, reg, self._display, special_items=self.special_items)
            temp.getBody(self._story, indexedFlowable=self._indexedFlowable, level=1)
            self._story.append(PageBreak())


class RegistrantsListToPDF(PDFBase):

    def __init__(self, conf, doc=None, story=[], reglist=None, display=[], special_items=None):
        self._conf = conf
        self._regList = reglist
        self._display = display
        PDFBase.__init__(self, doc, story, printLandscape=True)
        self._title = _("Registrants List")
        self._PAGE_HEIGHT = landscape(A4)[1]
        self._PAGE_WIDTH = landscape(A4)[0]
        self.special_items = special_items

    def firstPage(self, c, doc):
        c.saveState()
        showLogo = False
        c.setFont('Times-Bold', 30)
        if not showLogo:
            self._drawWrappedString(c, escape(self._conf.getTitle()), height=self._PAGE_HEIGHT-0.75*inch)
        c.setFont('Times-Bold', 25)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        c.setFont('Times-Roman', 10)
        c.drawRightString(self._PAGE_WIDTH - inch,self._PAGE_HEIGHT-1*cm, "%s"%(nowutc().strftime("%d %B %Y, %H:%M")))
        c.restoreState()

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story

        style = ParagraphStyle({})
        style.fontSize = 12
        style.alignment = TA_CENTER
        text = i18nformat("""<b>_("List of registrants")</b>""")
        p = Paragraph(text, style, part=escape(self._conf.getTitle()))
        p.spaceAfter = 30
        story.append(p)

        text_format = ParagraphStyle({})
        text_format.leading = 10
        text_format.fontName = "Times-Roman"
        text_format.fontSize = 8
        text_format.spaceBefore=0
        text_format.spaceAfter=0
        text_format.alignment=TA_LEFT
        text_format.leftIndent=10
        text_format.firstLineIndent=0

        tsRegs=TableStyle([('VALIGN',(0,0),(-1,-1),"MIDDLE"),
                        ('LINEBELOW',(0,0),(-1,0), 1, colors.black),
                        ('ALIGN',(0,0),(-1,0),"CENTER"),
                        ('ALIGN',(0,1),(-1,-1),"LEFT") ] )
        l = []
        lp = []
        lp.append(Paragraph('<b>{}</b>'.format(_('ID')), text_format))
        lp.append(Paragraph('<b>{}</b>'.format(_('Name')), text_format))

        accommodation_col_counter = 0
        for item in self._display:
            if item.input_type == 'accommodation':
                accommodation_col_counter += 1
                lp.append(Paragraph("<b>{}</b>".format(item.title.encode('utf-8')), text_format))
                lp.append(Paragraph("<b>{}</b>".format(_('Arrival date')), text_format))
                lp.append(Paragraph("<b>{}</b>".format(_('Departure date')), text_format))
            else:
                lp.append(Paragraph("<b>{}</b>".format(item.title.encode('utf-8')), text_format))
        if 'reg_date' in self.special_items:
            lp.append(Paragraph('<b>{}</b>'.format(_('Registration date')), text_format))
        if 'state' in self.special_items:
            lp.append(Paragraph('<b>{}</b>'.format(_('Registration state')), text_format))
        if 'price' in self.special_items:
            lp.append(Paragraph('<b>{}</b>'.format(_('Price')), text_format))
        if 'checked_in' in self.special_items:
            lp.append(Paragraph('<b>{}</b>'.format(_('Checked in')), text_format))
        if 'checked_in_date' in self.special_items:
            lp.append(Paragraph('<b>{}</b>'.format(_('Check-in date')), text_format))
        l.append(lp)

        for registration in self._regList:
            lp = []
            lp.append(Paragraph(registration.friendly_id, text_format))
            lp.append(Paragraph("{} {}".format(registration.first_name.encode('utf-8'),
                                               registration.last_name.encode('utf-8')), text_format))
            data = registration.data_by_field
            for item in self._display:
                friendly_data = data.get(item.id).friendly_data if data.get(item.id) else ''
                if item.input_type == 'accommodation':
                    if friendly_data:
                        friendly_data = data[item.id].friendly_data
                        lp.append(Paragraph(friendly_data['choice'].encode('utf-8'), text_format))
                        lp.append(Paragraph(format_date(friendly_data['arrival_date']), text_format))
                        lp.append(Paragraph(format_date(friendly_data['departure_date']), text_format))
                    else:
                        # Fill in with empty space to avoid breaking the layout
                        lp.append(Paragraph('', text_format))
                        lp.append(Paragraph('', text_format))
                        lp.append(Paragraph('', text_format))
                elif item.input_type == 'multi_choice':
                    if friendly_data:
                        multi_choice_data = ', '.join(friendly_data).encode('utf-8')
                        lp.append(Paragraph(multi_choice_data, text_format))
                    else:
                        lp.append(Paragraph('', text_format))
                else:
                    if isinstance(friendly_data, unicode):
                        friendly_data = friendly_data.encode('utf-8')
                    lp.append(Paragraph(str(friendly_data), text_format))
            if 'reg_date' in self.special_items:
                lp.append(Paragraph(format_datetime(registration.submitted_dt), text_format))
            if 'state' in self.special_items:
                lp.append(Paragraph(registration.state.title.encode('utf-8'), text_format))
            if 'price' in self.special_items:
                lp.append(Paragraph(registration.render_price(), text_format))
            if 'checked_in' in self.special_items:
                checked_in = 'Yes' if registration.checked_in else 'No'
                lp.append(Paragraph(checked_in, text_format))
            if 'checked_in_date' in self.special_items:
                check_in_date = format_datetime(registration.checked_in_dt) if registration.checked_in else ''
                lp.append(Paragraph(check_in_date, text_format))
            l.append(lp)
        noneList = (None,) * (len(self._display) + len(self.special_items) + (accommodation_col_counter * 2) + 2)
        t = Table(l, colWidths=noneList, style=tsRegs)
        self._story.append(t)
        return story


class RegistrantsListToBadgesPDF:
    """
    Class used to print the Badges for the registrants
    """

    """
    The following dictionary maps the names of the fonts, as returned by the javascript in WConfModifBadgeDesign.tpl,
    to actual TTF font names.
    Each font name is mapped to 4 TTF fonts: Normal one, Bold one, Italic one, Bold & Italic one.
    """
    __fonts = {'Times New Roman':['Times-Roman','Times-Bold','Times-Italic','Times-Bold-Italic'],
               'Courier':['Courier', 'Courier-Bold', 'Courier-Italic', 'Courier-Bold-Italic'],
               'Sans':['Sans', 'Sans-Bold', 'Sans-Italic', 'Sans-Bold-Italic'],
               'LinuxLibertine':['LinuxLibertine','LinuxLibertine-Bold','LinuxLibertine-Italic','LinuxLibertine-Bold-Italic'],
               'Kochi-Mincho':['Kochi-Mincho','Kochi-Mincho','Kochi-Mincho','Kochi-Mincho'],
               'Kochi-Gothic':['Kochi-Gothic','Kochi-Gothic','Kochi-Gothic','Kochi-Gothic'],
               'Uming-CN':['Uming-CN','Uming-CN','Uming-CN','Uming-CN']
           #,'Bitstream Cyberbit':['Bitstream-Cyberbit', 'Bitstream-Cyberbit', 'Bitstream-Cyberbit', 'Bitstream-Cyberbit']
               }

    """ The following dictionary maps the sizes of the items, as returned by the javascript in WConfModifBadgeDesign.tpl,
    to actual font sizes in points, as ReportLab needs.
    """
    __fontSizes = {'xx-small':9,
                   'x-small':10,
                   'small':11,
                   'medium':12,
                   'large':14,
                   'x-large':16,
                   'xx-large':24
                   }

    """ The following dictionary maps the possible text alignments, as returned by the javascript in WConfModifBadgeDesign.tpl,
    to ReportLab constants.
    """
    __alignments = {'Left':TA_LEFT,
                    'Right':TA_RIGHT,
                    'Center':TA_CENTER,
                    'Justified':TA_JUSTIFY
                    }

    """ The following dictionary maps the possible text colors, as returned by the javascript in WConfModifBadgeDesign.tpl,
    to ReportLab color constants.
    """
    __colors = {'black': colors.black,
                'red': colors.red,
                'blue': colors.blue,
                'green': colors.green,
                'yellow': colors.yellow,
                'brown': colors.brown,
                'cyan': colors.cyan,
                'gold': colors.gold,
                'pink': colors.pink,
                'gray': colors.gray,
                'white': colors.white
                }

    def __init__(self, conf, badgeTemplate, marginTop, marginBottom, marginLeft, marginRight, marginColumns, marginRows,
                 pagesize, drawDashedRectangles, registrantList, printLandscape):
        """ Constructor
                conf: the conference for which the badges are printed, as a Conference object.
                badgeTemplate: the template used, as a BadgeTemplate object.
                marginTop: a float indicating the top margin, in cm, int or float
                marginBottom: a float indicating the minimum bottom margin, in cm, int or float
                marginLeft: a float indicating the left margin, in cm, int or float
                marginRight: a float indicating the minimum right margin, in cm, int or float
                marginColumns: a float indicating the margin between columns of badges, in cm, int or float
                marginRows: a float indicating the margin between rows of badges, in cm, int or float
                pagesize: a string with the pagesize to used, e.g. 'A4', 'A3', 'Letter'
                registrantList: either a string whose value should be "all", either a list of registrant id's
                printLandscape: use landscape orientation
            The badges will be drawn aligned to the left.
        """

        self.__conf = conf
        self.__badgeTemplate = badgeTemplate
        self.__marginTop = marginTop
        self.__marginBottom = marginBottom
        self.__marginLeft = marginLeft
        self.__marginRight = marginRight
        self.__marginColumns = marginColumns
        self.__marginRows = marginRows
        if registrantList == 'all':
            self.__registrantList = (Registration
                                     .find(Registration.is_active, Registration.event_id == conf.id)
                                     .order_by(*Registration.order_by_name)
                                     .all())
        else:
            self.__registrantList = (Registration
                                     .find(Registration.id.in_(registrantList), Registration.is_active,
                                           Registration.event_id == conf.id)
                                     .order_by(*Registration.order_by_name)
                                     .all())

        self.__size = PDFSizes().PDFpagesizes[pagesize]
        if printLandscape:
            self.__size = landscape(self.__size)
        self.__width, self.__height = self.__size

        self.__drawDashedRectangles = drawDashedRectangles

        setTTFonts()


    def getPDFBin(self):
        """ Returns the data of the PDF file to be printed
        """

        self.__fileDummy = FileDummy()
        self.__canvas = canvas.Canvas(self.__fileDummy, pagesize=self.__size)

        nBadgesHorizontal = int((self.__width - self.__marginLeft * cm - self.__marginRight * cm + self.__marginColumns * cm  + 0.01*cm) /
                                ((self.__badgeTemplate.getWidthInCm() + self.__marginColumns)  * cm))


        nBadgesVertical = int((self.__height - self.__marginTop * cm - self.__marginBottom * cm + self.__marginRows * cm + 0.01*cm) /
                              ((self.__badgeTemplate.getHeightInCm() + self.__marginRows) * cm))

        # We get an instance of the position generator
        p = RegistrantsListToBadgesPDF.__position_generator(
                               nBadgesHorizontal, nBadgesVertical,
                               self.__badgeTemplate.getWidthInCm() * cm, self.__badgeTemplate.getHeightInCm() * cm,
                               self.__marginLeft * cm, self.__marginTop * cm, self.__marginColumns * cm, self.__marginRows * cm)

        if nBadgesHorizontal == 0 or nBadgesVertical == 0:
            raise NoReportError( _("The template dimensions are too large for the page size you selected"))

        # We print a badge for each registrant
        for registrant in self.__registrantList:
            try:
                posx, posy = p.next()
                self.__draw_badge(registrant, posx, posy)
            except StopIteration:
                # We have printed all the badges that fitted in 1 page, we have to restart the position generator.
                self.__canvas.showPage()
                p = RegistrantsListToBadgesPDF.__position_generator(
                               nBadgesHorizontal, nBadgesVertical,
                               self.__badgeTemplate.getWidthInCm() * cm, self.__badgeTemplate.getHeightInCm() * cm,
                               self.__marginLeft * cm, self.__marginTop * cm, self.__marginColumns * cm, self.__marginRows * cm)
                posx, posy = p.next()
                self.__draw_badge(registrant, posx, posy)

        self.__canvas.save()
        return self.__fileDummy.getData()

    def __position_generator(cls,
                             nBadgesHorizontal, nBadgesVertical,
                             badgeWidth, badgeHeight,
                             marginLeft, marginTop,
                             interColumnMargin, interRowMargin):
        """ Generates the a new position for drawing a badge each time it is called.
        The position of a badge is the position of the top left corner.
        When there are no more positions available in a page, it throws a StopIteration exception.
        """

        nx = 0
        ny = 0
        while ny < nBadgesVertical:
            while nx < nBadgesHorizontal:
                x = marginLeft + nx * (badgeWidth + interColumnMargin)
                y = marginTop + ny * (badgeHeight + interRowMargin)
                nx = nx + 1
                yield x,y
            nx = 0
            ny = ny + 1
        return
    __position_generator = classmethod(__position_generator)


    def __draw_badge(self, registrant, posx, posy):
        """ Draws a badge, for a given registrant, at the position (posx, posy).
        (posx, posy) is the position of the top left corner of a badge.
        """

        # We draw a dashed rectangle around the badge
        if self.__drawDashedRectangles:
            self.__canvas.saveState()
            self.__canvas.setDash(1,5)
            self.__canvas.rect(posx, self.__height - posy - self.__badgeTemplate.getHeightInCm() * cm,
                               self.__badgeTemplate.getWidthInCm() * cm, self.__badgeTemplate.getHeightInCm() * cm)
            self.__canvas.restoreState()

        # We draw the background if we find it.
        usedBackgroundId = self.__badgeTemplate.getUsedBackgroundId()
        if usedBackgroundId != -1 and self.__badgeTemplate.getBackground(usedBackgroundId)[1] is not None:
            self.__canvas.drawImage(self.__badgeTemplate.getBackground(usedBackgroundId)[1].getFilePath(),
                                    posx, self.__height - posy - self.__badgeTemplate.getHeightInCm() * cm,
                                    self.__badgeTemplate.getWidthInCm() * cm, self.__badgeTemplate.getHeightInCm() * cm)


        # We draw the items of the badge
        for item in self.__badgeTemplate.getItems():
            # First we determine the actual text that has to be drawed.
            action = BadgeDesignConfiguration().items_actions.get(item.getKey())
            action = action[1] if action else ''
            if isinstance(action, str):
                # If for this kind of item we have to draw always the same string, let's draw it.
                text = action
            elif isinstance(action, types.LambdaType):
                text = action(registrant)
                if isinstance(text, unicode):
                    text = text.encode('utf-8')
            elif isinstance(action, types.MethodType):
                # If the action is a method, depending on which class owns the method, we pass a
                # different object to the method.
                if action.im_class == conference.Conference:
                    text = action.__call__(registrant.registration_form.event)
                elif action.im_class == BadgeTemplateItem:
                    text = action.__call__(item)
                else:
                    text = _("Error")
            elif isinstance(action, types.ClassType):
                # If the action is a class, it must be a class who complies to the following interface:
                #  -it must have a getArgumentType() method, which returns either Conference, Registrant or BadgeTemplateItem.
                #  Depending on what is returned, we will pass a different object to the getValue() method.
                #  -it must have a getValue(object) method, to which a Conference instance, a Registrant instance or a
                #  BadgeTemplateItem instance must be passed, depending on the result of the getArgumentType() method.
                argumentType = action.getArgumentType()
                if argumentType == conference.Conference:
                    text = action.getValue(registrant.registration_form.event)
                elif argumentType == BadgeTemplateItem:
                    text = action.getValue(item)
                else:
                    text = _("Error")
            else:
                text = _("Error")

            if not isinstance(text, basestring):
                text = str(text)
            text = escape(text)

            #style definition for the Paragraph used to draw the text.
            style = ParagraphStyle({})
            style.alignment = RegistrantsListToBadgesPDF.__alignments[item.getTextAlign()]
            style.textColor = RegistrantsListToBadgesPDF.__colors[item.getColor()]
            style.fontSize = RegistrantsListToBadgesPDF.__fontSizes.get(item.getFontSize(), 25)
            style.leading = style.fontSize

            if item.isBold() and item.isItalic():
                style.fontName = style.fontName = RegistrantsListToBadgesPDF.__fonts[item.getFont()][3]
            elif item.isItalic():
                style.fontName = style.fontName = RegistrantsListToBadgesPDF.__fonts[item.getFont()][2]
            elif item.isBold():
                style.fontName = style.fontName = RegistrantsListToBadgesPDF.__fonts[item.getFont()][1]
            else:
                style.fontName = style.fontName = RegistrantsListToBadgesPDF.__fonts[item.getFont()][0]

            p = Paragraph(text, style)

            itemx = self.__badgeTemplate.pixelsToCm(item.getX()) * cm
            itemy = self.__badgeTemplate.pixelsToCm(item.getY()) * cm

            availableWidth = self.__badgeTemplate.pixelsToCm(item.getWidth()) * cm
            availableHeight = (self.__badgeTemplate.getHeightInCm()
                               - self.__badgeTemplate.pixelsToCm(item.getY()) \
                              ) * cm

            w,h = p.wrap(availableWidth, availableHeight)

            if w > availableWidth or h > availableHeight:
                ## TODO: give warnings
                pass

            p.drawOn(self.__canvas, posx + itemx, self.__height - posy - itemy - h)


class LectureToPosterPDF:
    """
    Class used to print a lecture's poster
    """

    """ The following dictionary maps the names of the fonts, as returned by the javascript in WConfModifPosterDesign.tpl,
    to actual TTF font names.
    Each font name is mapped to 4 TTF fonts: Normal one, Bold one, Italic one, Bold & Italic one.
    """
    __fonts = {'Times New Roman':['Times-Roman','Times-Bold','Times-Italic','Times-Bold-Italic'],
               'Courier':['Courier', 'Courier-Bold', 'Courier-Italic', 'Courier-Bold-Italic'],
               'Sans':['Sans', 'Sans-Bold', 'Sans-Italic', 'Sans-Bold-Italic'],
               'LinuxLibertine':['LinuxLibertine','LinuxLibertine-Bold','LinuxLibertine-Italic','LinuxLibertine-Bold-Italic'],
               'Kochi-Mincho':['Kochi-Mincho','Kochi-Mincho','Kochi-Mincho','Kochi-Mincho'],
               'Kochi-Gothic':['Kochi-Gothic','Kochi-Gothic','Kochi-Gothic','Kochi-Gothic'],
               'Uming-CN':['Uming-CN','Uming-CN','Uming-CN','Uming-CN']
           #,'Bitstream Cyberbit':['Bitstream-Cyberbit', 'Bitstream-Cyberbit', 'Bitstream-Cyberbit', 'Bitstream-Cyberbit']
               }


    """ The following dictionary maps the possible text alignments, as returned by the javascript in WConfModifPosterDesign.tpl,
    to ReportLab constants.
    """
    __alignments = {'Left':TA_LEFT,
                    'Right':TA_RIGHT,
                    'Center':TA_CENTER,
                    'Justified':TA_JUSTIFY
                    }

    """ The following dictionary maps the possible text colors, as returned by the javascript in WConfModifPosterDesign.tpl,
    to ReportLab color constants.
    """
    __colors = {'black': colors.black,
                'red': colors.red,
                'blue': colors.blue,
                'green': colors.green,
                'yellow': colors.yellow,
                'brown': colors.brown,
                'cyan': colors.cyan,
                'gold': colors.gold,
                'pink': colors.pink,
                'gray': colors.gray,
                'white': colors.white
                }


    def __init__(self, conf, posterTemplate, marginH, marginV, pagesize, tz=None):
        """ Constructor
        conf: the conference for which the posters are printed, as a Conference object.
        posterTemplate: the template used, as a PosterTemplate object.
        marginH: a number indicating the minimal horizontal margin
        marginV: a number indicating the minimal vertical margin
        pagesize: a string with the pagesize to used, e.g. 'A4', 'A3', 'Letter'
        registrantList: either a string whose value should be "all",
                        either a list of registrant id's
        """

        self.__conf = conf
        if not tz:
            self._tz = self.__conf.getTimezone()
        else:
            self._tz = tz
        self.__posterTemplate = posterTemplate
        self.__marginH = marginH
        self.__marginV = marginV

        self.__size = PDFSizes().PDFpagesizes[pagesize]
        self.__width, self.__height = self.__size

        setTTFonts()

    """ The following function maps the sizes of the items, as returned by the javascript in WConfModifPosterDesign.tpl,
    to actual font sizes in points, as ReportLab needs.
    """
    def __extract_size(cls, sizePt):

        m = re.match(r"(\d+)(pt)",sizePt)

        if m:
            return int(m.group(1))
        return None
    __extract_size = classmethod (__extract_size)


    def getPDFBin(self):
        """ Returns the data of the PDF file to be printed
        """

        self.__fileDummy = FileDummy()
        self.__canvas = canvas.Canvas(self.__fileDummy, pagesize = self.__size)

        self.__draw_poster(self.__marginH * cm, self.__marginV * cm)

        self.__canvas.save()
        return self.__fileDummy.getData()

    def __draw_background(self, file, position, posx, posy):

        img = Image.open(file)

        imgWidth, imgHeight = img.size

        posx = self.__posterTemplate.pixelsToCm(posx)
        posy = self.__posterTemplate.pixelsToCm(posy)

        if position == "Stretch":
            x_1 = posx
            y_1 = posy
            width = self.__posterTemplate.getWidthInCm()
            height = self.__posterTemplate.getHeightInCm()

        elif position == "Center":
            height = self.__posterTemplate.pixelsToCm(imgHeight)
            width = self.__posterTemplate.pixelsToCm(imgWidth)

            posterWidth = self.__posterTemplate.getWidthInCm()
            posterHeight = self.__posterTemplate.getHeightInCm()

            if width > posterWidth or height > posterHeight:

                if width > posterWidth:
                    ratio = float(posterWidth)/width
                    width = posterWidth
                    height = height*ratio

                    x_1 = posx
                    y_1 = posy + (posterHeight - height)/2.0


                if  height > posterHeight:
                    ratio = float(posterHeight)/height
                    height = posterHeight
                    width = width*ratio
                    x_1 = posx + (posterWidth - width)/2.0
                    y_1 = posy
            else:
                x_1 = posx + (posterWidth - self.__posterTemplate.pixelsToCm(imgWidth))/2.0
                y_1 = posy + (posterHeight - self.__posterTemplate.pixelsToCm(imgHeight))/2.0

        self.__canvas.drawImage(file,
                                x_1 * cm, y_1 * cm,
                                width * cm, height * cm)


    def __draw_poster(self, posx, posy):
        """ Draws a poster, for a given registrant, at the position (posx, posy).
        (posx, posy) is the position of the top left corner of a poster.
        """

        # We draw the background if we find it.
        usedBackgroundId = self.__posterTemplate.getUsedBackgroundId()

        if usedBackgroundId != -1 and self.__posterTemplate.getBackground(usedBackgroundId)[1] is not None:

            self.__draw_background(self.__posterTemplate.getBackground(usedBackgroundId)[1].getFilePath(),
                             self.__posterTemplate.getBackgroundPosition(usedBackgroundId),posx,posy)

        # We draw the items of the poster
        for item in self.__posterTemplate.getItems():

            # First we determine the actual text that has to be drawed.
            action = PosterDesignConfiguration().items_actions[item.getKey()][1]

            if isinstance(action, str):
                # If for this kind of item we have to draw always the same string, let's draw it.
                # text is passed in lists, because some fields need several lines
                text = [action]
            elif isinstance(action, types.MethodType):
                # If the action is a method, depending on which class owns the method, we pass a
                # different object to the method.
                if action.im_class == conference.Conference:
                    text = action.__call__(self.__conf).replace("\r\n","\n").split("\n")
                elif action.im_class == PosterTemplateItem:
                    text = [action.__call__(item)]
                else:
                    text= [_("Error")]
            elif isinstance(action, types.ClassType):
                # If the action is a class, it must be a class who complies to the following interface:
                #  -it must have a getArgumentType() method, which returns either Conference or PosterTemplateItem.
                #  Depending on what is returned, we will pass a different object to the getValue() method.
                #  -it must have a getValue(object) method, to which a Conference instance or a
                #  PosterTemplateItem instance must be passed, depending on the result of the getArgumentType() method.
                argumentType = action.getArgumentType()
                if action.__name__ == "ConferenceChairperson":
                    #this specific case may need more than one line
                    chairList = action.getValue(self.__conf)

                    # 'text' is a list of lines
                    text = []
                    # let's fill it with the chairpersons' names
                    for chair in chairList:
                        if chair.getAffiliation() != "":
                            text.append("%s (%s)" % (chair.getDirectFullName(),chair.getAffiliation()))
                        else:
                            text.append(chair.getDirectFullName())

                elif argumentType == conference.Conference:
                    text = [action.getValue(self.__conf)]
                elif argumentType == PosterTemplateItem:
                    text = [action.getValue(item)]
                else:
                    text = [_("Error")]
            else:
                text = [_("Error")]

            text = map(escape,text)

            #style definition for the Paragraph used to draw the text.
            style = ParagraphStyle({})
            style.alignment = LectureToPosterPDF.__alignments[item.getTextAlign()]
            style.textColor = LectureToPosterPDF.__colors[item.getColor()]
            style.fontSize = LectureToPosterPDF.__extract_size(item.getFontSize())
            style.leading = style.fontSize

            if item.isBold() and item.isItalic():
                style.fontName = style.fontName = LectureToPosterPDF.__fonts[item.getFont()][3]
            elif item.isItalic():
                style.fontName = style.fontName = LectureToPosterPDF.__fonts[item.getFont()][2]
            elif item.isBold():
                style.fontName = style.fontName = LectureToPosterPDF.__fonts[item.getFont()][1]
            else:
                style.fontName = style.fontName = LectureToPosterPDF.__fonts[item.getFont()][0]

            availableWidth = self.__posterTemplate.pixelsToCm(item.getWidth()) * cm
            availableHeight = (self.__posterTemplate.getHeightInCm()
                               - self.__posterTemplate.pixelsToCm(item.getY()) \
                              ) * cm

            w,h = 0,0
            itemx = self.__posterTemplate.pixelsToCm(item.getX()) * cm
            itemy = self.__posterTemplate.pixelsToCm(item.getY()) * cm

            # now, we iterate over the line set
            for line in text:
                if line == "":
                    itemy += style.fontSize
                else:
                    p = Paragraph(line, style)

                    itemy += h

                    w,h = p.wrap(availableWidth, availableHeight)

                    if w > availableWidth or h > availableHeight:
                        ## TODO: warnings
                        pass

                    # finally, draw
                    p.drawOn(self.__canvas, posx + itemx, self.__height - posy - itemy - h)


class TicketToPDF(PDFBase):

    def __init__(self, conf, registration, doc=None, story=None):
        self._conf = conf
        self._registration = registration
        PDFBase.__init__(self, doc, story)

    def firstPage(self, c, doc):
        c.saveState()
        height = self._PAGE_HEIGHT - 1*cm
        width = 1*cm

        # Conference title
        height -= 1*cm
        startHeight = self._drawWrappedString(c, escape(self._conf.getTitle()),
                                              height=height, width=width, size=20,
                                              align="left", font='Times-Bold')

        # Conference start and end date
        height = startHeight - 1*cm
        self._drawWrappedString(c, "%s - %s" % (
            format_date(self._conf.getStartDate(), format='full'),
            format_date(self._conf.getEndDate(), format='full')),
            height=height, width=width, align="left", font="Times-Italic",
            size=15)

        # Conference location
        if self._conf.getLocation():
            height -= 0.7*cm
            self._drawWrappedString(
                c,
                escape(self._conf.getLocation().getName()),
                height=height, width=width, size=15, align="left",
                font="Times-Italic")

        # e-Ticket
        c.setFont('Times-Bold', 30)
        height -= 2*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0, height, _("e-ticket"))

        # QRCode (Version 6 with error correction L can contain up to 106 bytes)
        height -= 6*cm
        qr = QRCode(
            version=6,
            error_correction=constants.ERROR_CORRECT_M,
            box_size=4,
            border=1
        )
        config = Config.getInstance()
        baseURL = config.getBaseSecureURL() if config.getBaseSecureURL() else config.getBaseURL()
        qr_data = {"registrant_id": self._registration.id,
                   "checkin_secret": self._registration.ticket_uuid,
                   "event_id": self._conf.getId(),
                   "server_url": baseURL
                   }
        json_qr_data = json.dumps(qr_data)
        qr.add_data(json_qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image()

        c.drawImage(ImageReader(qr_img._img), width, height, height=4*cm,
                    width=4*cm)

        # QRCode and registrant info separating line
        width += 4.5*cm
        c.setStrokeColorRGB(0, 0, 0)
        c.line(width, height, width, height + 4*cm)

        # Registrant info
        width += 0.5*cm
        height += 3*cm
        self._drawWrappedString(c, escape("ID: {0}".format(self._registration.friendly_id)),
                                height=height, width=width, size=15,
                                align="left", font='Times-Roman')
        height -= 0.5*cm
        self._drawWrappedString(c, escape(self._registration.full_name),
                                height=height, width=width, size=15,
                                align="left", font='Times-Roman')
        personal_data = self._registration.get_personal_data()
        if personal_data.get('affiliation'):
            height -= 0.5*cm
            self._drawWrappedString(c,
                                    escape(personal_data['affiliation']),
                                    height=height, width=width, size=15,
                                    align="left", font='Times-Roman')
        if personal_data.get('address'):
            height -= 0.5*cm
            self._drawWrappedString(c, escape(personal_data['address']),
                                    height=height, width=width, size=15,
                                    align="left", font='Times-Roman')
        c.restoreState()
