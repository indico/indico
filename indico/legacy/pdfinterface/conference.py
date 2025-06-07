# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# ruff: noqa: N802, N803, N806, E741

import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import Table, TableStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.rl_config import defaultPageSize
from speaklater import is_lazy_string

from indico.legacy.pdfinterface.base import PageBreak, Paragraph, PDFBase, PDFWithTOC, Spacer, escape
from indico.modules.events.layout.util import get_menu_entry_by_name
from indico.modules.events.registration.models.items import PersonalDataType
from indico.modules.events.tracks.models.groups import TrackGroup
from indico.modules.events.tracks.settings import track_settings
from indico.util.date_time import format_date, format_datetime, now_utc
from indico.util.i18n import _
from indico.util.string import format_full_name, render_markdown, sanitize_for_platypus, strip_tags, truncate


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
    for style in styles.byName.values():
        if hasattr(style, 'fontName'):
            style.fontName = _font_map.get(style.fontName, style.fontName)
        if hasattr(style, 'bulletFontName'):
            style.bulletFontName = _font_map.get(style.bulletFontName, style.bulletFontName)
    return styles


class ProgrammeToPDF(PDFBase):
    def __init__(self, event, tz=None):
        self.event = event
        self._tz = self.event.tzinfo
        self._title = get_menu_entry_by_name('program', event).localized_title
        PDFBase.__init__(self, title='program.pdf')

    def firstPage(self, c, doc):
        c.saveState()

        height = self._drawLogo(c)

        if not height:
            height = self._drawWrappedString(c, escape(strip_tags(self.event.title)),
                                             height=self._PAGE_HEIGHT - 2*inch)

        c.setFont('Times-Bold', 15)

        height -= 2 * cm

        c.drawCentredString(self._PAGE_WIDTH/2.0, height, '{} - {}'.format(
            format_date(self.event.start_dt, format='full', timezone=self._tz),
            format_date(self.event.end_dt, format='full', timezone=self._tz)))
        if self.event.venue_name:
            height -= 1*cm
            c.drawCentredString(self._PAGE_WIDTH / 2.0, height, escape(self.event.venue_name))
        c.setFont('Times-Bold', 30)
        height -= 6*cm
        c.drawCentredString(self._PAGE_WIDTH/2.0, height, self._title)
        self._drawWrappedString(c, f'{strip_tags(self.event.title)} / {self._title}',
                                width=inch, height=0.75*inch, font='Times-Roman', size=9, color=(0.5, 0.5, 0.5),
                                align='left', maximumWidth=self._PAGE_WIDTH-3.5*inch, measurement=inch,
                                lineSpacing=0.15)
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch,
                          format_date(now_utc(), format='full', timezone=self._tz))
        c.restoreState()

    def laterPages(self, c, doc):
        c.saveState()
        self._drawWrappedString(c, f'{escape(strip_tags(self.event.title))} / {self._title}',
                                width=inch, height=self._PAGE_HEIGHT-0.75*inch, font='Times-Roman', size=9,
                                color=(0.5, 0.5, 0.5), align='left', maximumWidth=self._PAGE_WIDTH - 3.5*inch,
                                measurement=inch, lineSpacing=0.15)
        c.drawCentredString(self._PAGE_WIDTH/2.0, 0.75 * inch, _('Page {}').format(doc.page))
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch,
                          format_date(now_utc(), format='full', timezone=self._tz))
        c.restoreState()

    def _markdown_to_reportlab(self, markdown):
        html = sanitize_for_platypus(render_markdown(markdown))
        parts = []
        for i, part in enumerate(re.split(r'\n+', html)):
            if i > 0 and re.match(r'<(p|ul|ol)\b[^>]*>', part):
                # extra spacing before a block-level element
                parts.append('<br/>')
            parts.append(part)
        return '\n<br/>\n'.join(parts)

    def getBody(self, story=None):
        if not story:
            story = self._story
        styles = _get_sans_style_sheet()
        style = styles['Normal']
        style.alignment = TA_JUSTIFY
        styles['Heading2'].leftIndent = 20

        story.append(Paragraph(self._markdown_to_reportlab(track_settings.get(self.event, 'program')), style))

        story.append(Spacer(1, 0.4*inch))
        items = self.event.get_sorted_tracks()
        for item in items:
            self._story.append(Paragraph(escape(item.title), styles['Heading1']))
            story.append(Paragraph(self._markdown_to_reportlab(item.description), style))
            if isinstance(item, TrackGroup) and item.tracks:
                for track in item.tracks:
                    self._story.append(Paragraph(escape(track.title), styles['Heading2']))
                    story.append(Paragraph(self._markdown_to_reportlab(track.description), style))
            story.append(Spacer(1, 0.4*inch))


class RegistrantToPDF(PDFBase):
    def __init__(self, event, reg, display, doc=None, story=None, static_items=None):
        self.event = event
        self._reg = reg
        self._display = display
        self.static_items = static_items
        if not story:
            story = [Spacer(inch, 5*cm)]
        PDFBase.__init__(self, doc, story)
        self._title = _('Registrant')
        self._PAGE_HEIGHT = defaultPageSize[1]
        self._PAGE_WIDTH = defaultPageSize[0]

    def firstPage(self, c, doc):
        c.saveState()
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self.event.title), height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 25)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        c.setFont('Times-Roman', 10)
        c.restoreState()

    def getBody(self, story=None, indexedFlowable=None, level=1):
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
            if isinstance(caption, str) or is_lazy_string(caption):
                caption = str(caption)
            if isinstance(value, str) or is_lazy_string(value):
                value = str(value)
            text = f'<b>{caption}</b>: {value}'
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
                                           abbrev_first_name=False)

        header_style = ParagraphStyle({}, style, fontSize=16)
        header_data = [
            [Paragraph(full_name_title, header_style),
             Paragraph(f'#{registration.friendly_id}',
                       ParagraphStyle({}, header_style, alignment=TA_RIGHT))],
        ]
        header_table_style = TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0),
                                         ('RIGHTPADDING', (0, 0), (-1, -1), 0)])
        tbl = Table(header_data, style=header_table_style, colWidths=[None, cm])
        story.append(tbl)
        indexedFlowable[tbl] = {'text': registration.full_name, 'level': 1}

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
            if 'tags_present' in self.static_items and registration.tags:
                tags = ', '.join(sorted(t.title for t in registration.tags))
                _print_row(_('Tags'), tags)

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
            elif item.input_type == 'sessions' and item.id in data:
                sessions_data = '; '.join(data[item.id].friendly_data)
                _print_row(item.title, sessions_data)
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
        self._title = _('Registrants Book')
        self._static_item_ids = static_item_ids
        PDFWithTOC.__init__(self)

    def firstPage(self, c, doc):
        c.saveState()
        c.setFont('Times-Bold', 30)
        if not self._drawLogo(c):
            self._drawWrappedString(c, escape(self.event.title),
                                    height=self._PAGE_HEIGHT - 2*inch)
        c.setFont('Times-Bold', 35)
        c.drawCentredString(self._PAGE_WIDTH/2, self._PAGE_HEIGHT/2, self._title)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        # c.line(inch, self._PAGE_HEIGHT - inch - 6*cm, self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - inch - 6*cm)
        # c.line(inch, inch , self._PAGE_WIDTH - inch, inch)
        c.setFont('Times-Roman', 10)
        c.drawString(0.5*inch, 0.5*inch, self.event.short_external_url)
        c.restoreState()

    def laterPages(self, c, doc):
        c.saveState()
        c.setFont('Times-Roman', 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        confTitle = escape(truncate(self.event.title, 30))
        c.drawString(inch, self._PAGE_HEIGHT - 0.75 * inch, f'{confTitle} / {self._title}')
        title = truncate(doc.getCurrentPart(), 50)
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 0.75 * inch, f'{title}')
        c.drawRightString(self._PAGE_WIDTH - inch, 0.75 * inch, ' {} {} '.format(_('Page'), doc.page))
        c.drawString(inch, 0.75 * inch, format_date(now_utc(), format='full', timezone=self.event.tzinfo))
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
    def __init__(self, event, doc=None, story=None, reglist=None, display=None, static_items=None):
        if display is None:
            display = []
        if story is None:
            story = []
        self.event = event
        self._regList = reglist
        self._display = display
        PDFBase.__init__(self, doc, story, printLandscape=True)
        self._title = _('Registrants List')
        self._PAGE_HEIGHT = landscape(A4)[1]
        self._PAGE_WIDTH = landscape(A4)[0]
        self.static_items = static_items

    def firstPage(self, c, doc):
        c.saveState()
        showLogo = False
        c.setFont('Times-Bold', 30)
        if not showLogo:
            self._drawWrappedString(c, escape(self.event.title),
                                    height=self._PAGE_HEIGHT - 0.75*inch)
        c.setFont('Times-Bold', 25)
        c.setLineWidth(3)
        c.setStrokeGray(0.7)
        c.setFont('Times-Roman', 10)
        c.drawRightString(self._PAGE_WIDTH - inch, self._PAGE_HEIGHT - 1*cm,
                          format_date(now_utc(), format='full', timezone=self.event.tzinfo))
        c.restoreState()

    def getBody(self, story=None, indexedFlowable=None, level=1):
        if indexedFlowable is None:
            indexedFlowable = {}
        if not story:
            story = self._story

        style = ParagraphStyle({})
        style.fontName = 'Sans'
        style.fontSize = 12
        style.alignment = TA_CENTER
        text = '<b>{}</b>'.format(_('List of registrants'))
        p = Paragraph(text, style, part=escape(self.event.title))
        p.spaceAfter = 30
        story.append(p)

        text_format = ParagraphStyle({})
        text_format.leading = 10
        text_format.fontName = 'Times-Roman'
        text_format.fontSize = 8
        text_format.spaceBefore = 0
        text_format.spaceAfter = 0
        text_format.alignment = TA_LEFT
        text_format.leftIndent = 10
        text_format.firstLineIndent = 0

        tsRegs = TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Sans'),
                             ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                             ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                             ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                             ('ALIGN', (0, 1), (-1, -1), 'LEFT')])
        l = []
        lp = []
        lp.append(Paragraph('<b>{}</b>'.format(_('ID')), text_format))
        lp.append(Paragraph('<b>{}</b>'.format(_('Name')), text_format))

        accommodation_col_counter = 0
        for item in self._display:
            if item.input_type == 'accommodation':
                accommodation_col_counter += 1
                lp.append(Paragraph(f'<b>{escape(item.title)}</b>', text_format))
                lp.append(Paragraph('<b>{}</b>'.format(_('Arrival date')), text_format))
                lp.append(Paragraph('<b>{}</b>'.format(_('Departure date')), text_format))
            else:
                lp.append(Paragraph(f'<b>{escape(item.title)}</b>', text_format))
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
        if 'tags_present' in self.static_items:
            lp.append(Paragraph('<b>{}</b>'.format(_('Tags')), text_format))
        l.append(lp)

        for registration in self._regList:
            lp = []
            lp.append(Paragraph(registration.friendly_id, text_format))
            lp.append(Paragraph(f'{escape(registration.first_name)} {escape(registration.last_name)}', text_format))
            data = registration.data_by_field
            for item in self._display:
                friendly_data = data.get(item.id).friendly_data if data.get(item.id) else ''
                if item.input_type == 'accommodation':
                    if friendly_data:
                        friendly_data = data[item.id].friendly_data
                        lp.append(Paragraph(escape(friendly_data['choice']), text_format))
                        lp.append(Paragraph(format_date(friendly_data['arrival_date']), text_format))
                        lp.append(Paragraph(format_date(friendly_data['departure_date']), text_format))
                    else:
                        # Fill in with empty space to avoid breaking the layout
                        lp.append(Paragraph('', text_format))
                        lp.append(Paragraph('', text_format))
                        lp.append(Paragraph('', text_format))
                elif item.input_type == 'multi_choice':
                    if friendly_data:
                        multi_choice_data = ', '.join(friendly_data)
                        lp.append(Paragraph(escape(multi_choice_data), text_format))
                    else:
                        lp.append(Paragraph('', text_format))
                elif item.input_type == 'sessions':
                    if friendly_data:
                        sessions_data = '; '.join(friendly_data)
                        lp.append(Paragraph(escape(sessions_data), text_format))
                    else:
                        lp.append(Paragraph('', text_format))
                else:
                    lp.append(Paragraph(escape(str(friendly_data)), text_format))
            if 'reg_date' in self.static_items:
                lp.append(Paragraph(format_datetime(registration.submitted_dt), text_format))
            if 'state' in self.static_items:
                lp.append(Paragraph(registration.state.title, text_format))
            if 'price' in self.static_items:
                lp.append(Paragraph(registration.render_price(), text_format))
            if 'checked_in' in self.static_items:
                checked_in = 'Yes' if registration.checked_in else 'No'
                lp.append(Paragraph(checked_in, text_format))
            if 'checked_in_date' in self.static_items:
                check_in_date = format_datetime(registration.checked_in_dt) if registration.checked_in else ''
                lp.append(Paragraph(check_in_date, text_format))
            if 'tags_present' in self.static_items:
                tags = ', '.join(sorted(t.title for t in registration.tags))
                lp.append(Paragraph(escape(tags), text_format))
            l.append(lp)
        noneList = (None,) * (len(self._display) + len(self.static_items) + (accommodation_col_counter * 2) + 2)
        t = Table(l, colWidths=noneList, style=tsRegs)
        self._story.append(t)
        return story
