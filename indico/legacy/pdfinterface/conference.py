# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

# ruff: noqa: N802

import re

from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, inch

from indico.legacy.pdfinterface.base import Paragraph, PDFBase, Spacer, escape
from indico.modules.events.layout.util import get_menu_entry_by_name
from indico.modules.events.tracks.models.groups import TrackGroup
from indico.modules.events.tracks.settings import track_settings
from indico.util.date_time import format_date, now_utc
from indico.util.i18n import _
from indico.util.string import render_markdown, sanitize_for_platypus, strip_tags


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
