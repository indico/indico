# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# flake8: noqa

import re
from copy import deepcopy
from datetime import timedelta
from operator import attrgetter

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import Table, TableStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.rl_config import defaultPageSize
from speaklater import is_lazy_string

from indico.core.db import db
from indico.legacy.common import utils
from indico.legacy.pdfinterface.base import PageBreak, Paragraph, PDFBase, PDFWithTOC, Spacer, escape, modifiedFontSize
from indico.modules.events.layout.util import get_menu_entry_by_name
from indico.modules.events.registration.models.items import PersonalDataType
from indico.modules.events.timetable.models.entries import TimetableEntry, TimetableEntryType
from indico.modules.events.tracks.models.groups import TrackGroup
from indico.modules.events.tracks.settings import track_settings
from indico.util.date_time import format_date, format_datetime, format_human_timedelta, format_time, now_utc
from indico.util.i18n import _, ngettext
from indico.util.string import (format_full_name, html_color_to_rgb, natural_sort_key, render_markdown,
                                sanitize_for_platypus, strip_tags, to_unicode, truncate)


# Change reportlab default pdf font Helvetica to indico ttf font,
# because of better support for international characters.
# Default font can't be easily changed by setting new value to
# reportlab.rl_config.canvas_basefontname, because this variable
# is used directly to initialize state of several reportlab modules
# during their (first) import.
def _get_sans_style_sheet():
    _font_map = {
        'Helvetica': 'Sans',
        'Helvetica-Bold': 'Sans-Bold',
        'Helvetica-Oblique': 'Sans-Italic',
        'Helvetica-BoldOblique': 'Sans-Bold-Italic',
    }

    styles = getSampleStyleSheet()
    for name, style in styles.byName.iteritems():
        if hasattr(style, 'fontName'):
            style.fontName = _font_map.get(style.fontName, style.fontName)
        if hasattr(style, 'bulletFontName'):
            style.bulletFontName = _font_map.get(style.bulletFontName, style.bulletFontName)
    return styles


class ProgrammeToPDF(PDFBase):

    def __init__(self, event, tz=None):
        self.event = event
        self._tz = self.event.tzinfo
        self._title = get_menu_entry_by_name('program', event).localized_title.encode('utf-8')
        PDFBase.__init__(self, title='program.pdf')

    def firstPage(self, c, doc):
        c.saveState()

        height = self._drawLogo(c)

        if not height:
            height = self._drawWrappedString(c, escape(strip_tags(self.event.title).encode('utf-8')),
                                             height=self._PAGE_HEIGHT - 2*inch)

        c.setFont('Times-Bold', 15)

        height -= 2 * cm

        c.drawCentredString(self._PAGE_WIDTH/2.0, height, "{} - {}".format(
            self.event.start_dt_local.strftime("%A %d %B %Y"), self.event.end_dt_local.strftime("%A %d %B %Y")))
        if self.event.venue_name:
            height-=1*cm
            c.drawCentredString(self._PAGE_WIDTH / 2.0, height, escape(self.event.venue_name.encode('utf-8')))
        c.setFont('Times-Bold', 30)
        height-=6*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0, height, self._title)
        self._drawWrappedString(c, "%s / %s" % (strip_tags(self.event.title).encode('utf-8'), self._title),
                                width=inch, height=0.75*inch, font='Times-Roman', size=9, color=(0.5,0.5,0.5), align="left", maximumWidth=self._PAGE_WIDTH-3.5*inch, measurement=inch, lineSpacing=0.15)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, now_utc().strftime("%A %d %B %Y"))
        c.restoreState()

    def laterPages(self, c, doc):
        c.saveState()
        self._drawWrappedString(c, "%s / %s" % (escape(strip_tags(self.event.title).encode('utf-8')), self._title),
                                width=inch, height=self._PAGE_HEIGHT-0.75*inch, font='Times-Roman', size=9,
                                color=(0.5, 0.5, 0.5), align="left", maximumWidth=self._PAGE_WIDTH - 3.5*inch,
                                measurement=inch, lineSpacing=0.15)
        c.drawCentredString(self._PAGE_WIDTH/2.0, 0.75 * inch, "Page %d "%doc.page)
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, now_utc().strftime("%A %d %B %Y"))
        c.restoreState()

    def getBody(self, story=None):
        if not story:
            story = self._story
        styles = _get_sans_style_sheet()
        style = styles["Normal"]
        style.alignment = TA_JUSTIFY
        styles["Heading2"].leftIndent = 20

        event_program = sanitize_for_platypus(render_markdown(track_settings.get(self.event, 'program')))
        parts = []
        for i, part in enumerate(re.split(r'\n+', event_program)):
            if i > 0 and re.match(r'<(p|ul|ol)\b[^>]*>', part):
                # extra spacing before a block-level element
                parts.append(u'<br/>')
            parts.append(part)
        story.append(Paragraph(u'\n<br/>\n'.join(parts).encode('utf-8'), style))

        story.append(Spacer(1, 0.4*inch))
        items = self.event.get_sorted_tracks()
        for item in items:
            bogustext = item.title.encode('utf-8')
            p = Paragraph(escape(bogustext), styles["Heading1"])
            self._story.append(p)
            bogustext = item.description.encode('utf-8')
            p = Paragraph(escape(bogustext), style)
            story.append(p)
            if isinstance(item, TrackGroup) and item.tracks:
                for track in item.tracks:
                    bogustext = track.title.encode('utf-8')
                    p = Paragraph(escape(bogustext), styles["Heading2"])
                    self._story.append(p)
                    bogustext = track.description.encode('utf-8')
                    p = Paragraph(escape(bogustext), style)
                    story.append(p)
            story.append(Spacer(1, 0.4*inch))


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
        self.contribPosterAbstract = not params.get('dontShowPosterAbstract', True)
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
    def __init__(self, event, user, showSessions=None, showDays=None, sortingCrit=None, ttPDFFormat=None,
                 pagesize='A4', fontsize='normal', firstPageNumber=1, showSpeakerAffiliation=False,
                 showSessionDescription=False, tz=None):
        self.event = event
        self._user = user
        self._tz = event.display_tzinfo.zone
        self._showSessions = showSessions
        self._showDays = showDays
        self._ttPDFFormat = ttPDFFormat or TimetablePDFFormat()
        story = None if self._ttPDFFormat.showCoverPage() else []
        PDFWithTOC.__init__(self, story=story, pagesize=pagesize, fontsize=fontsize, firstPageNumber=firstPageNumber,
                            include_toc=self._ttPDFFormat.showTableContents())
        self._title = _("Programme")
        self._doc.leftMargin = 1 * cm
        self._doc.rightMargin = 1 * cm
        self._doc.topMargin = 1 * cm
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
                style2.fontName = "Sans"
                style2.fontSize = modifiedFontSize(14, self._fontsize)
                style2.leading = modifiedFontSize(10, self._fontsize)
                style2.alignment = TA_CENTER
                sess_captions = [sess.title for sess in self.event.sessions if sess.id in self._showSessions]
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

            height = self._drawWrappedString(c, self.event.title.encode('utf-8'))
            c.setFont('Times-Bold', modifiedFontSize(15, self._fontsize))
            height -= 2 * cm
            c.drawCentredString(self._PAGE_WIDTH / 2.0, height,
                                "{} - {}".format(format_date(self.event.start_dt, format='full', timezone=self._tz),
                                                 format_date(self.event.end_dt, format='full', timezone=self._tz)))
            if self.event.venue_name:
                height -= 2 * cm
                c.drawCentredString(self._PAGE_WIDTH / 2.0, height, escape(self.event.venue_name))
            c.setFont('Times-Bold', modifiedFontSize(30, self._fontsize))
            height -= 1 * cm
            c.drawCentredString(self._PAGE_WIDTH / 2.0, height, self._title)
            self._drawWrappedString(c, "{} / {}".format(self.event.title.encode('utf-8'), self._title),
                                    width=inch,
                                    height=0.75 * inch, font='Times-Roman', size=modifiedFontSize(9, self._fontsize),
                                    color=(0.5, 0.5, 0.5), align="left", maximumWidth=self._PAGE_WIDTH - 3.5 * inch,
                                    measurement=inch, lineSpacing=0.15)
            c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, now_utc().strftime("%A %d %B %Y"))
            c.restoreState()

    def laterPages(self, c, doc):
        c.saveState()
        maxi = self._PAGE_WIDTH - 2 * cm
        if doc.getCurrentPart().strip():
            maxi = self._PAGE_WIDTH - 6 * cm
        self._drawWrappedString(c, "{} / {}".format(self.event.title.encode('utf-8'), self._title),
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

        stylesheet = _get_sans_style_sheet()
        dayStyle = stylesheet["Heading1"]
        dayStyle.fontSize = modifiedFontSize(dayStyle.fontSize, self._fontsize)
        self._styles["day"] = dayStyle

        sessionTitleStyle = stylesheet["Heading2"]
        sessionTitleStyle.fontSize = modifiedFontSize(12.0, self._fontsize)
        self._styles["session_title"] = sessionTitleStyle

        sessionDescriptionStyle = stylesheet["Heading2"]
        sessionDescriptionStyle.fontSize = modifiedFontSize(10.0, self._fontsize)
        self._styles["session_description"] = sessionDescriptionStyle

        contribDescriptionStyle = stylesheet["Normal"]
        contribDescriptionStyle.fontSize = modifiedFontSize(9.0, self._fontsize)
        self._styles["contrib_description"] = contribDescriptionStyle

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
        if not contrib.can_access(self._user):
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
            if not subc.can_access(self._user):
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
        if not contrib.can_access(self._user):
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
            if not subc.can_access(self._user):
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
        style = _get_sans_style_sheet()["Normal"]
        style.fontSize = modifiedFontSize(fSize, self._fontsize)
        style.leading = modifiedFontSize(fSize + 3, self._fontsize)
        return Paragraph(text, style)

    def _fontifyRow(self, row, fSize=10, fName=""):
        return [self._fontify(text, fSize, fName) for text in row]

    def _processDayEntries(self, day, story):
        res = []
        originalts = TableStyle([('FONTNAME', (0, 0), (-1, -1), "Sans"),
                                 ('VALIGN', (0, 0), (-1, -1), "TOP"),
                                 ('LEFTPADDING', (0, 0), (-1, -1), 1),
                                 ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                                 ('GRID', (0, 1), (-1, -1), 1, colors.lightgrey)])
        self._tsSpk = TableStyle([('FONTNAME', (0, 0), (-1, -1), "Sans"),
                                  ("LEFTPADDING", (0, 0), (0, -1), 0),
                                  ("RIGHTPADDING", (0, 0), (0, -1), 0),
                                  ("TOPPADDING", (0, 0), (0, -1), 1),
                                  ("BOTTOMPADDING", (0, 0), (0, -1), 0)])
        colorts = TableStyle([('FONTNAME', (0, 0), (-1, -1), "Sans"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 3),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("TOPPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                              ('GRID', (0, 0), (0, -1), 1, colors.lightgrey)])
        entries = (self.event.timetable_entries
                   .filter(db.cast(TimetableEntry.start_dt.astimezone(self.event.tzinfo), db.Date) == day,
                           TimetableEntry.parent_id.is_(None))
                   .order_by(TimetableEntry.start_dt)
                   .all())
        for entry in entries:
            # Session slot
            if entry.type == TimetableEntryType.SESSION_BLOCK:
                sess_block = entry.object
                if self._showSessions and sess_block.session.id not in self._showSessions:
                    continue
                if not sess_block.can_access(self._user):
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
                    for contrib in sorted(contribs, key=lambda x: natural_sort_key(x.board_number)):
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

                            if self._ttPDFFormat.showLengthContribs():
                                caption = u'{} ({})'.format(obj.title, format_human_timedelta(s_entry.duration))
                            else:
                                caption = obj.title

                            lt.append([self._fontify(caption.encode('utf-8'), 10)])
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
                            widths = [0.95 * cm, None]
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
                if not contrib.can_access(self._user):
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
                if self._ttPDFFormat.showContribAbstract():
                    p3 = Paragraph(escape(unicode(contrib.description)), self._styles["contrib_description"])
                    res.append(p3)
                if entry == entries[-1]:  # if it is the last one, we do the page break and remove the previous one.
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
            p = Paragraph(escape(self.event.title.encode('utf-8')), s)
            story.append(p)
            story.append(Spacer(1, 0.4 * inch))

        current_day = self.event.start_dt.date()
        end_day = self.event.end_dt.date()
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
    def __init__(self, event, user, showSessions=[], showDays=[], sortingCrit=None, ttPDFFormat=None, pagesize='A4',
                 fontsize='normal', tz=None):
        self.event = event
        self._tz = tz or self.event.timezone
        self._user = user
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
        stylesheets = _get_sans_style_sheet()

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
        """Check if the session has slots with titles or not."""
        for ss in session.blocks:
            if ss.title.strip():
                return True
        return False

    def _processDayEntries(self, day, story):
        lastSessions = []  # this is to avoid checking if the slots have titles for all the slots
        res = []
        entries = (self.event.timetable_entries
                   .filter(db.cast(TimetableEntry.start_dt.astimezone(self.event.tzinfo), db.Date) == day,
                           TimetableEntry.parent_id.is_(None))
                   .order_by(TimetableEntry.start_dt))
        for entry in entries:
            if entry.type == TimetableEntryType.SESSION_BLOCK:
                session_slot = entry.object
                sess = session_slot.session
                if self._showSessions and sess.id not in self._showSessions:
                    continue
                if not session_slot.can_access(self._user):
                    continue
                if sess in lastSessions:
                    continue
                if self._haveSessionSlotsTitles(sess):
                    e = session_slot
                else:
                    lastSessions.append(sess)
                    e = sess
                title = e.title
                res.append(Paragraph(u'<font face="Times-Bold"><b> {}:</b></font> {}'
                                     .format(_(u"Session"), escape(title)).encode('utf-8'),
                                     self._styles["normal"]))
                room_time = escape(session_slot.room_name) if session_slot.room_name else u''
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
                if not contrib.can_access(self._user):
                    continue

                res.append(Paragraph(u'<font face="Times-Bold"><b> {}:</b></font> {}'
                                     .format(_(u"Contribution"), escape(contrib.title)), self._styles["normal"]))

                room_time = escape(contrib.room_name) if contrib.room_name else u''
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
                                     .format(_(u"Break"), escape(title)), self._styles["normal"]))
                room_time = escape(break_.room_name) if break_.room_name else u''
                room_time = (u'<font face="Times-Bold"><b> {}:</b></font> {}({}-{})'
                             .format(_(u"Time and Place"), room_time,
                                     to_unicode(format_date(entry.start_dt, timezone=self._tz)),
                                     to_unicode(format_date(entry.end_dt, timezone=self._tz))))
                res.append(Paragraph(room_time, self._styles["normal"]))
                res.append(Spacer(1, 0.2 * inch))
        res.append(PageBreak())
        return res

    def getBody(self, story=None):
        self._defineStyles()
        if not story:
            story = self._story

        current_day = self.event.start_dt.date()
        end_day = self.event.end_dt.date()
        while current_day <= end_day:
            if len(self._showDays) > 0 and current_day.strftime("%d-%B-%Y") not in self._showDays:
                current_day += timedelta(days=1)
                continue

            day_entries = self._processDayEntries(current_day, story)
            if not day_entries:
                current_day += timedelta(days=1)
                continue
            text = u'{} - {}-{}'.format(
                escape(self.event.title),
                escape(to_unicode(format_date(self.event.start_dt, timezone=self._tz))),
                escape(to_unicode(format_date(self.event.end_dt, timezone=self._tz)))
            )
            if self.event.venue_name:
                text = u'%s, %s.' % (text, escape(self.event.venue_name))
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
    def __init__(self, event, reg, display, doc=None, story=None, static_items=None):
        self.event = event
        self._reg = reg
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
            self._drawWrappedString(c, escape(self.event.title.encode('utf-8')),
                                    height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 25)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        c.setFont('Times-Roman', 10)
        c.restoreState()

    def getBody(self, story=None, indexedFlowable=None, level=1 ):
        if not story:
            story = self._story
        style = ParagraphStyle({})
        style.fontName = 'Sans'
        style.fontSize = 12

        registration = self._reg
        data = registration.data_by_field

        def _append_text_to_story(text, space=0.2, style=style):
            p = Paragraph(text, style, registration.full_name)
            story.append(p)
            story.append(Spacer(inch, space*cm, registration.full_name))

        def _print_row(caption, value):
            if isinstance(caption, unicode) or is_lazy_string(caption):
                caption = unicode(caption).encode('utf-8')
            if isinstance(value, unicode) or is_lazy_string(value):
                value = unicode(value).encode('utf-8')
            text = '<b>{field_name}</b>: {field_value}'.format(field_name=caption, field_value=value)
            _append_text_to_story(text)

        def _print_section(caption):
            story.append(Spacer(0, 20))
            section_style = ParagraphStyle({})
            section_style.fontSize = 13
            section_style.textColor = (0.5, 0.5, 0.5)
            _append_text_to_story(caption, style=section_style)
            story.append(HRFlowable(width='100%', thickness=1, color=(0.8, 0.8, 0.8), lineCap='round',
                                    spaceAfter=10, dash=None))

        full_name_title = format_full_name(registration.first_name, registration.last_name,
                                           registration.get_personal_data().get('title'),
                                           last_name_first=False, last_name_upper=False,
                                           abbrev_first_name=False, show_title=True)

        header_style = ParagraphStyle({}, style, fontSize=16)
        header_data = [
            [Paragraph(full_name_title.encode('utf-8'), header_style),
             Paragraph('#{}'.format(registration.friendly_id),
                       ParagraphStyle({}, header_style, alignment=TA_RIGHT))],
        ]
        header_table_style = TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0),
                                         ('RIGHTPADDING', (0, 0), (-1, -1), 0)])
        tbl = Table(header_data, style=header_table_style, colWidths=[None, cm])
        story.append(tbl)
        indexedFlowable[tbl] = {'text': registration.full_name.encode('utf-8'), 'level': 1}

        style = ParagraphStyle({})
        style.fontName = 'Sans'
        style.alignment = TA_JUSTIFY

        if self.static_items:
            _print_section(_('Registration details'))

            if 'reg_date' in self.static_items:
                _print_row(_('Registration date'), format_datetime(registration.submitted_dt))
            if 'state' in self.static_items:
                _print_row(_('Registration state'), registration.state.title)
            if 'price' in self.static_items:
                _print_row(_('Price'), registration.render_price())
            if 'payment_date' in self.static_items:
                payment_date = format_datetime(registration.payment_dt) if registration.payment_dt else ''
                _print_row(_('Payment date'), payment_date)
            if 'checked_in' in self.static_items:
                checked_in = 'Yes' if registration.checked_in else 'No'
                _print_row(_('Checked in'), checked_in)
            if 'checked_in_date' in self.static_items:
                check_in_date = format_datetime(registration.checked_in_dt) if registration.checked_in else ''
                _print_row(_('Check-in date'), check_in_date)

        for item in self._display:
            if item.input_type == 'accommodation' and item.id in data:
                _print_row(item.title, data[item.id].friendly_data.get('choice'))
                arrival_date = data[item.id].friendly_data.get('arrival_date')
                _print_row(_('Arrival date'), format_date(arrival_date) if arrival_date else '')
                departure_date = data[item.id].friendly_data.get('departure_date')
                _print_row(_('Departure date'), format_date(departure_date) if departure_date else '')
            elif item.input_type == 'multi_choice' and item.id in data:
                multi_choice_data = ', '.join(data[item.id].friendly_data)
                _print_row(item.title, multi_choice_data)
            elif item.is_section:
                _print_section(item.title)
            elif item.personal_data_type in (PersonalDataType.title, PersonalDataType.first_name,
                                             PersonalDataType.last_name):
                continue
            else:
                value = data[item.id].friendly_data if item.id in data else ''
                _print_row(item.title, value)

        return story


class RegistrantsListToBookPDF(PDFWithTOC):
    def __init__(self, event, regform, reglist, item_ids, static_item_ids):
        self.event = event
        self._regform = regform
        self._regList = reglist
        self._item_ids = set(item_ids)
        self._title = _("Registrants Book")
        self._static_item_ids = static_item_ids
        PDFWithTOC.__init__(self)

    def firstPage(self, c, doc):
        c.saveState()
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self.event.title.encode('utf-8')),
                                    height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 35)
        c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT/2, self._title)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        #c.line(inch, self._PAGE_HEIGHT - inch - 6*cm, self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - inch - 6*cm)
        #c.line(inch, inch , self._PAGE_WIDTH - inch, inch)
        c.setFont('Times-Roman', 10)
        c.drawString(0.5*inch, 0.5*inch, self.event.short_external_url)
        c.restoreState()

    def laterPages(self, c, doc):
        c.saveState()
        c.setFont('Times-Roman', 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        confTitle = escape(truncate(self.event.title, 30).encode('utf-8'))
        c.drawString(inch, self._PAGE_HEIGHT - 0.75 * inch, "%s / %s"%(confTitle, self._title))
        title = doc.getCurrentPart()
        if len(doc.getCurrentPart())>50:
            title = utils.unicodeSlice(doc.getCurrentPart(), 0, 50) + "..."
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, "%s"%title)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, u" {} {} ".format(_(u"Page"), doc.page))
        c.drawString(inch,  0.75 * inch, now_utc().strftime("%A %d %B %Y"))
        c.restoreState()

    def getBody(self):
        items = []
        for section in self._regform.sections:
            if not section.is_visible:
                continue
            fields = [field for field in section.fields if field.id in self._item_ids and field.is_visible]
            if not fields:
                continue
            items.append(section)
            items += fields
        for reg in self._regList:
            temp = RegistrantToPDF(self.event, reg, items, static_items=self._static_item_ids)
            temp.getBody(self._story, indexedFlowable=self._indexedFlowable, level=1)
            self._story.append(PageBreak())


class RegistrantsListToPDF(PDFBase):
    def __init__(self, event, doc=None, story=[], reglist=None, display=[], static_items=None):
        self.event = event
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
            self._drawWrappedString(c, escape(self.event.title.encode('utf-8')),
                                    height=self._PAGE_HEIGHT - 0.75*inch)
        c.setFont('Times-Bold', 25)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        c.setFont('Times-Roman', 10)
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 1*cm, now_utc().strftime("%d %B %Y, %H:%M"))
        c.restoreState()

    def getBody(self, story=None, indexedFlowable={}, level=1 ):
        if not story:
            story = self._story

        style = ParagraphStyle({})
        style.fontName = "Sans"
        style.fontSize = 12
        style.alignment = TA_CENTER
        text = u'<b>{}</b>'.format(_(u"List of registrants"))
        p = Paragraph(text, style, part=escape(self.event.title.encode('utf-8')))
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

        tsRegs = TableStyle([('FONTNAME', (0, 0), (-1, -1), "Sans"),
                             ('VALIGN', (0, 0), (-1, -1), "MIDDLE"),
                             ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                             ('ALIGN', (0, 0), (-1, 0), "CENTER"),
                             ('ALIGN', (0, 1), (-1, -1), "LEFT")])
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
