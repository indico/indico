# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from copy import deepcopy
from datetime import timedelta
from itertools import takewhile
from operator import attrgetter

from pytz import timezone
from qrcode import QRCode, constants
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from reportlab.rl_config import defaultPageSize
from speaklater import is_lazy_string

from indico.core.config import Config
from indico.core.db import db
from indico.modules.events.abstracts.models.abstracts import AbstractState, AbstractReviewingState
from indico.modules.events.abstracts.models.reviews import AbstractAction
from indico.modules.events.abstracts.settings import boa_settings, BOASortField, BOACorrespondingAuthorType
from indico.modules.events.layout.util import get_menu_entry_by_name
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.modules.events.tracks.settings import track_settings
from indico.modules.events.util import create_event_logo_tmp_file
from indico.util import json
from indico.util.date_time import format_date, format_datetime, format_time, format_human_timedelta
from indico.util.i18n import ngettext, _
from indico.util.string import html_color_to_rgb, to_unicode, truncate
from indico.legacy.pdfinterface.base import (escape, PDFLaTeXBase, PDFBase, PDFWithTOC, Paragraph, Spacer, PageBreak,
                                             modifiedFontSize)
from indico.legacy.common import utils
from indico.legacy.common.timezoneUtils import DisplayTZ, nowutc
from indico.legacy.webinterface.common.tools import strip_ml_tags

styles = getSampleStyleSheet()


def extract_affiliations(contrib):
    affiliations = dict()

    def enumerate_affil(person_links):
        auth_list = []

        for person_link in person_links:
            affil = person_link.affiliation
            if affil and affil not in affiliations:
                affiliations[affil] = len(affiliations) + 1
            auth_list.append((person_link, affiliations[affil] if affil else None))
        return auth_list

    authors = enumerate_affil(contrib.primary_authors)
    coauthors = enumerate_affil(contrib.secondary_authors)
    return affiliations, authors, coauthors


class ProgrammeToPDF(PDFBase):

    def __init__(self, event, tz=None):
        self._event = event
        self._conf = event.as_legacy
        self._tz = self._event.tzinfo
        self._title = get_menu_entry_by_name('program', event).localized_title.encode('utf-8')
        PDFBase.__init__(self, title='program.pdf')

    def firstPage(self, c, doc):
        c.saveState()

        height = self._drawLogo(c)

        if not height:
            height = self._drawWrappedString(c, escape(self._event.title.encode('utf-8')),
                                             height=self._PAGE_HEIGHT - 2*inch)

        c.setFont('Times-Bold', 15)

        height -= 2 * cm

        c.drawCentredString(self._PAGE_WIDTH/2.0, height, "{} - {}".format(
            self._event.start_dt_local.strftime("%A %d %B %Y"), self._event.end_dt_local.strftime("%A %d %B %Y")))
        if self._event.venue_name:
            height-=1*cm
            c.drawCentredString(self._PAGE_WIDTH / 2.0, height, escape(self._event.venue_name.encode('utf-8')))
        c.setFont('Times-Bold', 30)
        height-=6*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0, height, self._title)
        self._drawWrappedString(c, "%s / %s" % (strip_ml_tags(self._event.title.encode('utf-8')), self._title),
                                width=inch, height=0.75*inch, font='Times-Roman', size=9, color=(0.5,0.5,0.5), align="left", maximumWidth=self._PAGE_WIDTH-3.5*inch, measurement=inch, lineSpacing=0.15)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()

    def laterPages(self, c, doc):
        c.saveState()
        self._drawWrappedString(c, "%s / %s" % (escape(strip_ml_tags(self._event.title.encode('utf-8'))), self._title),
                                width=inch, height=self._PAGE_HEIGHT-0.75*inch, font='Times-Roman', size=9,
                                color=(0.5, 0.5, 0.5), align="left", maximumWidth=self._PAGE_WIDTH - 3.5*inch,
                                measurement=inch, lineSpacing=0.15)
        c.drawCentredString(self._PAGE_WIDTH/2.0, 0.75 * inch, "Page %d "%doc.page)
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()

    def getBody(self, story=None):
        if not story:
            story = self._story
        style = styles["Normal"]
        style.alignment = TA_JUSTIFY
        p = Paragraph(escape(track_settings.get(self._event, 'program').encode('utf-8')), style)
        story.append(p)
        story.append(Spacer(1, 0.4*inch))
        for track in self._event.tracks:
            bogustext = track.title.encode('utf-8')
            p = Paragraph(escape(bogustext), styles["Heading1"])
            self._story.append(p)
            bogustext = track.description.encode('utf-8')
            p = Paragraph(escape(bogustext), style)
            story.append(p)
            story.append(Spacer(1, 0.4*inch))


class AbstractToPDF(PDFLaTeXBase):

    _tpl_filename = 'single_doc.tpl'

    def __init__(self, abstract, tz=None):
        super(AbstractToPDF, self).__init__()

        self._abstract = abstract
        event = abstract.event_new

        if tz is None:
            tz = event.timezone

        self._args.update({
            'doc_type': 'abstract',
            'abstract': abstract,
            'conf': event.as_legacy,
            'tz': timezone(tz),
            'track_class': self._get_track_classification(abstract),
            'contrib_type': self._get_contrib_type(abstract),
            'fields': [f for f in event.contribution_fields if f.is_active]
        })
        if event.logo:
            self._args['logo_img'] = create_event_logo_tmp_file(event).name

    @staticmethod
    def _get_track_classification(abstract):
        if abstract.state == AbstractState.accepted:
            if abstract.accepted_track:
                return escape(abstract.accepted_track.full_title)
        else:
            tracks = sorted(abstract.submitted_for_tracks | abstract.reviewed_for_tracks, key=attrgetter('position'))
            return u'; '.join(escape(t.full_title) for t in tracks)

    @staticmethod
    def _get_contrib_type(abstract):
        is_accepted = abstract.state == AbstractState.accepted
        return abstract.accepted_contrib_type if is_accepted else abstract.submitted_contrib_type


class AbstractsToPDF(PDFLaTeXBase):

    _tpl_filename = "report.tpl"

    def __init__(self, event, abstracts, tz=None):
        super(AbstractsToPDF, self).__init__()
        if tz is None:
            self._tz = event.timezone

        self._args.update({
            'conf': event.as_legacy,
            'doc_type': 'abstract',
            'title': _("Report of Abstracts"),
            'get_track_classification': AbstractToPDF._get_track_classification,
            'get_contrib_type': AbstractToPDF._get_contrib_type,
            'items': abstracts,
            'fields': [f for f in event.contribution_fields if f.is_active]
        })


class ConfManagerAbstractToPDF(AbstractToPDF):

    def __init__(self, abstract, tz=None):
        super(ConfManagerAbstractToPDF, self).__init__(abstract, tz)

        self._args.update({
            'doc_type': 'abstract_manager',
            'status': self._get_status(abstract),
            'track_judgements': self._get_track_reviewing_states(abstract)
        })

    @staticmethod
    def _get_status(abstract):
        state_title = abstract.state.title.upper()
        if abstract.state == AbstractState.duplicate:
            return _(u"{} (#{}: {})").format(state_title, abstract.duplicate_of.friendly_id,
                                             abstract.duplicate_of.title)
        elif abstract.state == AbstractState.merged:
            return _(u"{} (#{}: {})").format(state_title, abstract.merged_into.friendly_id, abstract.merged_into.title)
        else:
            return abstract.state.title.upper()

    @staticmethod
    def _get_track_reviewing_states(abstract):
        def _format_review_action(review):
            action = unicode(review.proposed_action.title)
            if review.proposed_action == AbstractAction.accept and review.proposed_contribution_type:
                return u'{}: {}'.format(action, review.proposed_contribution_type.name)
            else:
                return action

        reviews = []
        for track in abstract.reviewed_for_tracks:
            track_review_state = abstract.get_track_reviewing_state(track)
            review_state = track_review_state.title
            track_reviews = abstract.get_reviews(group=track)
            review_details = [(_format_review_action(review),
                               review.user.get_full_name(abbrev_first_name=False),
                               review.comment)
                              for review in track_reviews]
            if track_review_state in {AbstractReviewingState.positive, AbstractReviewingState.conflicting}:
                proposed_contrib_types = {r.proposed_contribution_type.name for r in track_reviews
                                          if r.proposed_contribution_type}
                if proposed_contrib_types:
                    contrib_types = u', '.join(proposed_contrib_types)
                    review_state = u'{}: {}'.format(review_state, contrib_types)
            elif track_review_state == AbstractReviewingState.mixed:
                other_tracks = {x.title for r in track_reviews for x in r.proposed_tracks}
                proposed_actions = {x.proposed_action for x in track_reviews}
                no_track_actions = proposed_actions - {AbstractAction.change_tracks}
                other_info = []
                if no_track_actions:
                    other_info.append(u', '.join(unicode(a.title) for a in no_track_actions))
                if other_tracks:
                    other_info.append(_(u"Proposed for other tracks: {}").format(u', '.join(other_tracks)))
                if other_info:
                    review_state = u'{}: {}'.format(review_state, u'; '.join(other_info))

            elif track_review_state not in {AbstractReviewingState.negative, AbstractReviewingState.conflicting}:
                continue
            reviews.append((track.title, review_state, review_details))
        return reviews


class ConfManagerAbstractsToPDF(AbstractsToPDF):

    def __init__(self, event, abstracts, tz=None):
        super(ConfManagerAbstractsToPDF, self).__init__(event, abstracts, tz)

        self._args.update({
            'doc_type': 'abstract_manager',
            'get_status': ConfManagerAbstractToPDF._get_status,
            'get_track_judgements': ConfManagerAbstractToPDF._get_track_reviewing_states
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
            'tz': timezone(tz or event.timezone),
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
            'url': event.short_external_url,
            'tz': timezone(tz or event.timezone)
        })

        if event.logo:
            self.temp_file = create_event_logo_tmp_file(event)
            self._args['logo_img'] = self.temp_file.name


class ContributionBook(PDFLaTeXBase):

    _tpl_filename = "contribution_list_boa.tpl"

    def _sort_contribs(self, contribs, sort_by):
        mapping = {'number': 'id', 'name': 'title'}
        if sort_by == BOASortField.schedule:
            key_func = lambda c: (c.start_dt is None, c.start_dt)
        elif sort_by == BOASortField.session_title:
            key_func = lambda c: (c.session is None, c.session.title.lower() if c.session else '')
        elif sort_by == BOASortField.speaker:
            def key_func(c):
                speakers = c.speakers
                if not c.speakers:
                    return True, None
                return False, speakers[0].get_full_name(last_name_upper=False, abbrev_first_name=False).lower()
        else:
            key_func = attrgetter(mapping.get(sort_by) or 'title')
        return sorted(contribs, key=key_func)

    def __init__(self, event, aw, contribs=None, tz=None, sort_by=""):
        super(ContributionBook, self).__init__()
        self._conf = event.as_legacy

        tz = tz or event.timezone
        contribs = self._sort_contribs(contribs or event.contributions, sort_by)
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
            if boa_settings.get(event, 'corresponding_author') == BOACorrespondingAuthorType.submitter:
                corresp_authors[contrib.id] = [pl.person.email for pl in contrib.person_links if pl.is_submitter]
            if boa_settings.get(event, 'corresponding_author') == BOACorrespondingAuthorType.speakers:
                corresp_authors[contrib.id] = [speaker.person.email for speaker in contrib.speakers]

        self._args.update({
            'affiliation_contribs': affiliation_contribs,
            'corresp_authors': corresp_authors,
            'contribs': contribs,
            'conf': event.as_legacy,
            'tz': timezone(tz or event.timezone),
            'url': event.url,
            'fields': [f for f in event.contribution_fields if f.is_active],
            'sorted_by': sort_by,
            'aw': aw,
            'boa_text': boa_settings.get(event, 'extra_text')
        })

        if event.logo:
            self.temp_file = create_event_logo_tmp_file(event)
            self._args['logo_img'] = self.temp_file.name


class AbstractBook(ContributionBook):

    _tpl_filename = "book_of_abstracts.tpl"
    _table_of_contents = True

    def __init__(self, event, tz=None):
        sort_by = boa_settings.get(event, 'sort_by')

        super(AbstractBook, self).__init__(event, None, sort_by=sort_by)
        self._args['show_ids'] = boa_settings.get(event, 'show_abstract_ids')

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
            self.contribsAtConfLevel = False
            self.breaksAtConfLevel = False
            self.dateCloseToSessions = False
            self.coverPage = True
            self.tableContents = True
            self.contribPosterAbstract = False
        else:
            self.setValues(params)

    def setValues(self, params):
        self.contribId = params.get('showContribId', True)
        self.speakerTitle = params.get('showSpeakerTitle', True)
        self.contribAbstract = params.get('showAbstract', False)
        self.contribPosterAbstract = params.get('dontShowPosterAbstract', True)
        self.newPagePerSession = params.get('newPagePerSession', False)
        self.useSessionColorCodes = params.get('useSessionColorCodes', False)
        self.showSessionTOC = params.get('showSessionTOC', False)
        self.lengthContribs = params.get('showLengthContribs', False)
        self.contribsAtConfLevel = params.get('showContribsAtConfLevel', False)
        self.breaksAtConfLevel = params.get('showBreaksAtConfLevel', False)
        self.dateCloseToSessions = params.get('printDateCloseToSessions', False)
        self.coverPage = params.get('showCoverPage', False)
        self.tableContents = params.get('showTableContents', False)
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


class TimeTablePlain(PDFWithTOC):
    def __init__(self, event, aw, showSessions=None, showDays=None, sortingCrit=None, ttPDFFormat=None,
                 pagesize='A4', fontsize='normal', firstPageNumber=1, showSpeakerAffiliation=False,
                 showSessionDescription=False, tz=None):
        self._conf = event.as_legacy
        self._event = event
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
        self._showSessionDescription = showSessionDescription

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

            height = self._drawWrappedString(c, self._event.title.encode('utf-8'))
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
            self._drawWrappedString(c, "{} / {}".format(self._event.title.encode('utf-8'), self._title),
                                    width=inch,
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
        self._drawWrappedString(c, "{} / {}".format(self._event.title.encode('utf-8'), self._title),
                                width=1 * cm,
                                height=self._PAGE_HEIGHT - 1 * cm, font='Times-Roman',
                                size=modifiedFontSize(9, self._fontsize), color=(0.5, 0.5, 0.5), align="left",
                                lineSpacing=0.3, maximumWidth=maxi)
        c.drawCentredString(self._PAGE_WIDTH / 2.0, 0.5 * cm,
                            _('Page {}').format(doc.page + self._firstPageNumber - 1))
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
        speaker_name = speaker.get_full_name(last_name_first=True, show_title=self._ttPDFFormat.showSpeakerTitle(),
                                             abbrev_first_name=False)
        if self._showSpeakerAffiliation and speaker.affiliation:
            speaker_name += u' ({})'.format(speaker.affiliation)
        return speaker_name

    def _processContribution(self, contrib, l):
        if not contrib.can_access(self._aw):
            return

        lt = []
        date = format_time(contrib.start_dt, timezone=self._tz)
        caption = u'[{}] {}'.format(contrib.friendly_id, escape(contrib.title))

        if not self._ttPDFFormat.showContribId():
            caption = escape(contrib.title)
        elif self._ttPDFFormat.showLengthContribs():
            caption = u"{} ({})".format(caption, format_human_timedelta(contrib.timetable_entry.duration))
        elif self._ttPDFFormat.showContribAbstract():
            caption = u'<font face="Times-Bold"><b>{}</b></font>'.format(caption)

        color_cell = ""
        caption = u'<font size="{}">{}</font>'.format(unicode(modifiedFontSize(10, self._fontsize)), caption)
        lt.append([self._fontify(caption.encode('utf-8'), 10)])

        if self._useColors():
            color_cell = " "
        if self._ttPDFFormat.showContribAbstract():
            speaker_list = [self._get_speaker_name(spk) for spk in contrib.speakers]
            if speaker_list:
                speaker_title = u' {}: '.format(ngettext(u'Presenter', u'Presenters', len(speaker_list)))
                speaker_content = speaker_title + u', '.join(speaker_list)
                speaker_content = u'<font name="Times-Italic"><i>{}</i></font>'.format(speaker_content)
                lt.append([self._fontify(speaker_content, 9)])
            caption = escape(unicode(contrib.description))
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
            caption = '- [{}] {}'.format(subc.friendly_id, escape(subc.title.encode('utf-8')))
            if not self._ttPDFFormat.showContribId():
                caption = '- {}' .format(escape(subc.title.encode('utf-8')))
            elif self._ttPDFFormat.showLengthContribs():
                caption = '{} ({})'.format(caption, format_human_timedelta(subc.timetable_entry.duration))

            caption = '<font size="{}">{}</font>'.format(str(modifiedFontSize(10, self._fontsize)), caption)
            lt.append([Paragraph(caption, self._styles["subContrib"])])
            if self._ttPDFFormat.showContribAbstract():
                caption = '<font size="{}">{}</font>'.format(str(modifiedFontSize(9, self._fontsize)),
                                                             escape(unicode(subc.description)))
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
        caption_text = u"[{}] {}".format(contrib.friendly_id, escape(contrib.title))
        if not self._ttPDFFormat.showContribId():
            caption_text = escape(contrib.title)
        if self._ttPDFFormat.showLengthContribs():
            caption_text = u"{} ({})".format(caption_text, format_human_timedelta(contrib.duration))
        caption_text = u'<font name="Times-Bold">{}</font>'.format(caption_text)
        lt.append([self._fontify(caption_text.encode('utf-8'), 10)])
        board_number = contrib.board_number
        if self._ttPDFFormat.showContribAbstract() and self._ttPDFFormat.showContribPosterAbstract():
            speaker_list = [self._get_speaker_name(spk) for spk in contrib.speakers]
            if speaker_list:
                speaker_word = u'{}: '.format(ngettext(u'Presenter', u'Presenters', len(speaker_list)))
                speaker_text = speaker_word + ', '.join(speaker_list)
                speaker_text = u'<font face="Times-Italic"><i>{}</i></font>'.format(speaker_text)
                lt.append([self._fontify(speaker_text, 10)])
            caption_text = escape(unicode(contrib.description))
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
            caption_text = "- [{}] {}".format(subc.friendly_id, escape(subc.title.encode('utf-8')))
            if not self._ttPDFFormat.showContribId():
                caption_text = "- {}".format(subc.friendly_id)
            if self._ttPDFFormat.showLengthContribs():
                caption_text = "{} ({})".format(caption_text, escape(format_human_timedelta(subc.duration)))
            lt.append([Paragraph(caption_text, self._styles["subContrib"])])
            if self._ttPDFFormat.showContribAbstract():
                caption_text = u'<font size="{}">{}</font>'.format(str(modifiedFontSize(9, self._fontsize)),
                                                                   escape(unicode(subc.description)))
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
        entries = (self._event.timetable_entries
                   .filter(db.cast(TimetableEntry.start_dt.astimezone(self._event.tzinfo), db.Date) == day,
                           TimetableEntry.parent_id.is_(None))
                   .order_by(TimetableEntry.start_dt))
        for entry in entries:
            # Session slot
            if entry.type == TimetableEntryType.SESSION_BLOCK:
                sess_block = entry.object
                if self._showSessions and sess_block.session.id not in self._showSessions:
                    continue
                if not sess_block.can_access(self._aw):
                    continue

                room = u''
                if sess_block.room_name:
                    room = u' - {}'.format(escape(sess_block.room_name))

                session_caption = sess_block.full_title
                conv = []
                for c in sess_block.person_links:
                    if self._showSpeakerAffiliation and c.affiliation:
                        conv.append(u"{} ({})".format(escape(c.get_full_name(last_name_first=True,
                                                                             last_name_upper=False,
                                                                             abbrev_first_name=False)),
                                                      escape(c.affiliation)))
                    else:
                        conv.append(escape(c.full_name))

                conv = u'; '.join(conv)
                if conv:
                    conv = u'<font face="Times-Bold"><b>-{}: {}</b></font>'.format(_(u"Conveners"), conv)

                res.append(Paragraph('', self._styles["session_title"]))

                if self._ttPDFFormat.showDateCloseToSessions():
                    start_dt = to_unicode(format_datetime(sess_block.timetable_entry.start_dt, timezone=self._tz))
                else:
                    start_dt = to_unicode(format_time(sess_block.timetable_entry.start_dt, timezone=self._tz))

                sess_caption = u'<font face="Times-Bold">{}</font>'.format(escape(session_caption))
                text = u'<u>{}</u>{} ({}-{})'.format(
                    sess_caption, room, start_dt,
                    to_unicode(format_time(sess_block.timetable_entry.end_dt, timezone=self._tz)))

                p1 = Paragraph(text, self._styles["session_title"])
                if self._useColors():
                    ts = deepcopy(colorts)
                    ts.add('BACKGROUND', (0, 0), (0, -1), self._getSessionColor(sess_block))
                    p1 = Table([["", p1]], colWidths=[0.2 * cm, None], style=ts)

                res.append(p1)
                if self._ttPDFFormat.showTitleSessionTOC():
                    self._indexedFlowable[p1] = {'text': escape(sess_block.session.title.encode('utf-8')), 'level': 2}

                # add session description
                if self._showSessionDescription and sess_block.session.description:
                    text = u'<i>{}</i>'.format(escape(unicode(sess_block.session.description)))
                    res.append(Paragraph(text, self._styles["session_description"]))

                p2 = Paragraph(conv.encode('utf-8'), self._styles["conveners"])
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
                            caption = obj.title.encode('utf-8')

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
            # contribution
            elif self._ttPDFFormat.showContribsAtConfLevel() and entry.type == TimetableEntryType.CONTRIBUTION:
                contrib = entry.object
                if not contrib.can_access(self._aw):
                    continue

                room = u''
                if contrib.room_name:
                    room = u' - {}'.format(escape(contrib.room_name))

                speakers = u'; '.join([self._get_speaker_name(spk) for spk in contrib.speakers])
                if speakers.strip():
                    speaker_word = ngettext(u'Presenter', u'Presenters', len(contrib.speakers))
                    speakers = u'<font face="Times-Bold"><b>- {}: {}</b></font>'.format(speaker_word, speakers)

                text = u'<u>{}</u>{} ({}-{})'.format(escape(contrib.title), room,
                                                     to_unicode(format_time(entry.start_dt, timezone=self._tz)),
                                                     to_unicode(format_time(entry.end_dt, timezone=self._tz)))
                p1 = Paragraph(text.encode('utf-8'), self._styles["session_title"])
                res.append(p1)
                if self._ttPDFFormat.showTitleSessionTOC():
                    self._indexedFlowable[p1] = {'text': escape(contrib.title.encode('utf-8')), 'level': 2}

                p2 = Paragraph(speakers.encode('utf-8'), self._styles["conveners"])
                res.append(p2)
                if entry == entries[-1]:  # if it is the last one, we do the page break and remove the previous one.
                    res = list(takewhile(lambda x: not isinstance(x, PageBreak), res))
                    if self._ttPDFFormat.showNewPagePerSession():
                        res.append(PageBreak())
            # break
            elif self._ttPDFFormat.showBreaksAtConfLevel() and entry.type == TimetableEntryType.BREAK:
                break_entry = entry
                break_ = break_entry.object
                room = u''
                if break_.room_name:
                    room = u' - {}'.format(escape(break_.room_name))

                text = u'<u>{}</u>{} ({}-{})'.format(escape(break_.title), room,
                                                     to_unicode(format_time(break_entry.start_dt, timezone=self._tz)),
                                                     to_unicode(format_time(break_entry.end_dt, timezone=self._tz)))

                p1 = Paragraph(text.encode('utf-8'), self._styles["session_title"])
                res.append(p1)

                if self._ttPDFFormat.showTitleSessionTOC():
                    self._indexedFlowable[p1] = {'text': escape(break_.title.encode('utf-8')), 'level': 2}

                if entry == entries[-1]:  # if it is the last one, we do the page break and remove the previous one.
                    res = list(takewhile(lambda x: not isinstance(x, PageBreak), res))
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
            p = Paragraph(escape(self._event.title.encode('utf-8')), s)
            story.append(p)
            story.append(Spacer(1, 0.4 * inch))

        current_day = self._event.start_dt.date()
        end_day = self._event.end_dt.date()
        while current_day <= end_day:
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
    def __init__(self, event, aw, showSessions=[], showDays=[], sortingCrit=None, ttPDFFormat=None, pagesize='A4',
                 fontsize='normal', tz=None):
        self._conf = event.as_legacy
        self._event = event
        self._tz = tz or self._event.timezone
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
                   .filter(db.cast(TimetableEntry.start_dt.astimezone(self._event.tzinfo), db.Date) == day,
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
                res.append(Paragraph('<font face="Times-Bold"><b> {}:</b></font> {}'
                                     .format(_("Session"), escape(title.encode('utf-8'))),
                                     self._styles["normal"]))
                room_time = u""
                if session_slot.room_name:
                    room_time = to_unicode(escape(session_slot.room_name.encode('utf-8')))
                room_time = (u'<font face="Times-Bold"><b> {}:</b></font> {}({}-{})'
                             .format(_(u"Time and Place"), room_time,
                                     to_unicode(format_time(entry.start_dt, timezone=self._tz)),
                                     to_unicode(format_time(entry.end_dt, timezone=self._tz))))
                res.append(Paragraph(room_time, self._styles["normal"]))
                conveners = [c.full_name for c in session_slot.person_links]
                if conveners:
                    conveners_text = (u'<font face="Times-Bold"><b> {}:</b></font> {}'
                                      .format(ngettext(u'Convener', u'Conveners', len(conveners)),
                                              u'; '.join(conveners)))
                    res.append(Paragraph(conveners_text.encode('utf-8'), self._styles["normal"]))
                res.append(Spacer(1, 0.2 * inch))
            elif self._ttPDFFormat.showContribsAtConfLevel() and entry.type == TimetableEntryType.CONTRIBUTION:
                contrib = entry.object
                if not contrib.can_access(self._aw):
                    continue

                title = contrib.title
                res.append(Paragraph(u'<font face="Times-Bold"><b> {}:</b></font> {}'
                                     .format(_(u"Contribution"), escape(title.encode('utf-8'))), self._styles["normal"]))
                room_time = ""
                if contrib.room_name:
                    room_time = escape(contrib.room_name.encode('utf-8'))

                room_time = (u'<font face="Times-Bold"><b> {}:</b></font> {}({}-{})'
                             .format(_(u"Time and Place"), room_time,
                                     to_unicode(format_date(entry.start_dt, timezone=self._tz)),
                                     to_unicode(format_date(entry.end_dt, timezone=self._tz))))
                res.append(Paragraph(room_time, self._styles["normal"]))
                spks = [s.full_name for s in contrib.speakers]
                if spks:
                    speaker_word = u'{}: '.format(ngettext(u'Presenter', u'Presenters', len(spks)))
                    res.append(Paragraph(u'<font face="Times-Bold"><b> {}:</b></font> {}'
                                         .format(speaker_word, u"; ".join(spks)), self._styles["normal"]))
                res.append(Spacer(1, 0.2 * inch))
            elif self._ttPDFFormat.showBreaksAtConfLevel() and entry.type == TimetableEntryType.BREAK:
                break_ = entry.object
                title = break_.title
                res.append(Paragraph(u'<font face="Times-Bold"><b> {}:</b></font> {}'
                                     .format(_(u"Break"), escape(title.encode('utf-8'))), self._styles["normal"]))
                room_time = ""
                if break_.room_name:
                    room_time = escape(break_.room_name.encode('utf-8'))
                room_time = (u'<font face="Times-Bold"><b> {}:</b></font> {}({}-{})'
                             .format(_(u"Time and Place"), room_time, format_date(entry.start_dt, timezone=self._tz),
                                     format_date(entry.end_dt, timezone=self._tz)))
                res.append(Paragraph(room_time, self._styles["normal"]))
                res.append(Spacer(1, 0.2 * inch))
        res.append(PageBreak())
        return res

    def getBody(self, story=None):
        self._defineStyles()
        if not story:
            story = self._story

        current_day = self._event.start_dt.date()
        end_day = self._event.end_dt.date()
        while current_day <= end_day:
            if len(self._showDays) > 0 and current_day.strftime("%d-%B-%Y") not in self._showDays:
                current_day += timedelta(days=1)
                continue

            day_entries = self._processDayEntries(current_day, story)
            if not day_entries:
                current_day += timedelta(days=1)
                continue
            text = u'{} - {}-{}'.format(
                escape(self._event.title),
                escape(to_unicode(format_date(self._event.start_dt, timezone=self._tz))),
                escape(to_unicode(format_date(self._event.end_dt, timezone=self._tz)))
            )
            if self._event.venue_name:
                text = u'%s, %s.' % (text, self._event.venue_name)
            p = Paragraph(text.encode('utf-8'), self._styles["title"])
            story.append(p)
            text2 = u'{}: {}'.format(_(u'Daily Programme'), escape(current_day.strftime("%A %d %B %Y")))
            p2 = Paragraph(text2, self._styles["day"])
            story.append(p2)
            story.append(Spacer(1, 0.4 * inch))
            for entry in day_entries:
                story.append(entry)
            current_day += timedelta(days=1)


class RegistrantToPDF(PDFBase):

    def __init__(self, conf, reg, display, doc=None, story=None, static_items=None):
        self._reg = reg
        self._conf = conf
        self._display = display
        self.static_items = static_items
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
            self._drawWrappedString(c, escape(self._conf.as_event.title.encode('utf-8')),
                                    height=self._PAGE_HEIGHT - 2*inch)
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
            if isinstance(caption, unicode) or is_lazy_string(caption):
                caption = unicode(caption).encode('utf-8')
            if isinstance(value, unicode) or is_lazy_string(value):
                value = unicode(value).encode('utf-8')
            text = '<b>{field_name}</b>: {field_value}'.format(field_name=caption, field_value=value)
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

        if 'reg_date' in self.static_items:
            _print_row(caption=_('Registration date'), value=format_datetime(registration.submitted_dt))
        if 'state' in self.static_items:
            _print_row(caption=_('Registration state'), value=registration.state.title)
        if 'price' in self.static_items:
            _print_row(caption=_('Price'), value=registration.render_price())
        if 'checked_in' in self.static_items:
            checked_in = 'Yes' if registration.checked_in else 'No'
            _print_row(caption=_('Checked in'), value=checked_in)
        if 'checked_in_date' in self.static_items:
            check_in_date = format_datetime(registration.checked_in_dt) if registration.checked_in else ''
            _print_row(caption=_('Check-in date'), value=check_in_date)

        return story


class RegistrantsListToBookPDF(PDFWithTOC):
    def __init__(self, conf, doc=None, story=[], reglist=None, display=[], static_items=None):
        self._conf = conf
        self._regList = reglist
        self._display = display
        self._title = _("Registrants Book")
        self.static_items = static_items
        PDFWithTOC.__init__(self)

    def firstPage(self, c, doc):
        c.saveState()
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self._conf.as_event.title.encode('utf-8')),
                                    height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 35)
        c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT/2, self._title)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        #c.line(inch, self._PAGE_HEIGHT - inch - 6*cm, self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - inch - 6*cm)
        #c.line(inch, inch , self._PAGE_WIDTH - inch, inch)
        c.setFont('Times-Roman', 10)
        c.drawString(0.5*inch, 0.5*inch, self._conf.as_event.short_external_url)
        c.restoreState()

    def laterPages(self, c, doc):
        c.saveState()
        c.setFont('Times-Roman', 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        confTitle = escape(truncate(self._conf.as_event.title, 30).encode('utf-8'))
        c.drawString(inch, self._PAGE_HEIGHT - 0.75 * inch, "%s / %s"%(confTitle, self._title))
        title = doc.getCurrentPart()
        if len(doc.getCurrentPart())>50:
            title = utils.unicodeSlice(doc.getCurrentPart(), 0, 50) + "..."
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, "%s"%title)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, u" {} {} ".format(_(u"Page"), doc.page))
        c.drawString(inch,  0.75 * inch, nowutc().strftime("%A %d %B %Y"))
        c.restoreState()

    def getBody(self):
        for reg in self._regList:
            temp = RegistrantToPDF(self._conf, reg, self._display, static_items=self.static_items)
            temp.getBody(self._story, indexedFlowable=self._indexedFlowable, level=1)
            self._story.append(PageBreak())


class RegistrantsListToPDF(PDFBase):

    def __init__(self, conf, doc=None, story=[], reglist=None, display=[], static_items=None):
        self._conf = conf
        self._regList = reglist
        self._display = display
        PDFBase.__init__(self, doc, story, printLandscape=True)
        self._title = _("Registrants List")
        self._PAGE_HEIGHT = landscape(A4)[1]
        self._PAGE_WIDTH = landscape(A4)[0]
        self.static_items = static_items

    def firstPage(self, c, doc):
        c.saveState()
        showLogo = False
        c.setFont('Times-Bold', 30)
        if not showLogo:
            self._drawWrappedString(c, escape(self._conf.as_event.title.encode('utf-8')),
                                    height=self._PAGE_HEIGHT - 0.75*inch)
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
        text = u'<b>{}</b>'.format(_(u"List of registrants"))
        p = Paragraph(text, style, part=escape(self._conf.as_event.title.encode('utf-8')))
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
        if 'reg_date' in self.static_items:
            lp.append(Paragraph('<b>{}</b>'.format(_('Registration date')), text_format))
        if 'state' in self.static_items:
            lp.append(Paragraph('<b>{}</b>'.format(_('Registration state')), text_format))
        if 'price' in self.static_items:
            lp.append(Paragraph('<b>{}</b>'.format(_('Price')), text_format))
        if 'checked_in' in self.static_items:
            lp.append(Paragraph('<b>{}</b>'.format(_('Checked in')), text_format))
        if 'checked_in_date' in self.static_items:
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
            if 'reg_date' in self.static_items:
                lp.append(Paragraph(format_datetime(registration.submitted_dt), text_format))
            if 'state' in self.static_items:
                lp.append(Paragraph(registration.state.title.encode('utf-8'), text_format))
            if 'price' in self.static_items:
                lp.append(Paragraph(registration.render_price(), text_format))
            if 'checked_in' in self.static_items:
                checked_in = 'Yes' if registration.checked_in else 'No'
                lp.append(Paragraph(checked_in, text_format))
            if 'checked_in_date' in self.static_items:
                check_in_date = format_datetime(registration.checked_in_dt) if registration.checked_in else ''
                lp.append(Paragraph(check_in_date, text_format))
            l.append(lp)
        noneList = (None,) * (len(self._display) + len(self.static_items) + (accommodation_col_counter * 2) + 2)
        t = Table(l, colWidths=noneList, style=tsRegs)
        self._story.append(t)
        return story


class TicketToPDF(PDFBase):
    def __init__(self, event, registration, doc=None, story=None):
        self._event = event
        self._conf = event.as_legacy
        self._registration = registration
        PDFBase.__init__(self, doc, story)

    def firstPage(self, c, doc):
        c.saveState()
        height = self._PAGE_HEIGHT - 1*cm
        width = 1*cm

        # Conference title
        height -= 1*cm
        startHeight = self._drawWrappedString(c, escape(self._event.title.encode('utf-8')),
                                              height=height, width=width, size=20,
                                              align="left", font='Times-Bold')

        # Conference start and end date
        height = startHeight - 1*cm
        self._drawWrappedString(c, "%s - %s" % (
            format_date(self._event.start_dt_local, format='full'),
            format_date(self._event.end_dt_local, format='full')),
            height=height, width=width, align="left", font="Times-Italic",
            size=15)

        # Conference location
        if self._event.venue_name:
            height -= 0.7*cm
            self._drawWrappedString(
                c,
                escape(self._event.venue_name),
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
        qr_data = {"registrant_id": self._registration.id,
                   "checkin_secret": self._registration.ticket_uuid,
                   "event_id": self._event.id,
                   "server_url": config.getBaseURL()}
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
