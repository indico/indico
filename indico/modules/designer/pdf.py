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

from __future__ import unicode_literals

import re
from collections import namedtuple
from io import BytesIO

from PIL.Image import Image
from reportlab.lib import colors, pagesizes
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from indico.legacy.pdfinterface.base import setTTFonts
from indico.modules.designer import PageOrientation
from indico.web.flask.templating import strip_tags


FONT_STYLES = {
    'serif': ['Times-Roman', 'Times-Bold', 'Times-Italic', 'Times-Bold-Italic'],
    'courier': ['Courier', 'Courier-Bold', 'Courier-Italic', 'Courier-Bold-Italic'],
    'sans-serif': ['Sans', 'Sans-Bold', 'Sans-Italic', 'Sans-Bold-Italic'],
    'LinuxLibertine': ['LinuxLibertine', 'LinuxLibertine-Bold', 'LinuxLibertine-Italic', 'LinuxLibertine-Bold-Italic'],
    'Kochi-Mincho': ['Kochi-Mincho', 'Kochi-Mincho', 'Kochi-Mincho', 'Kochi-Mincho'],
    'Kochi-Gothic': ['Kochi-Gothic', 'Kochi-Gothic', 'Kochi-Gothic', 'Kochi-Gothic'],
    'Uming-CN': ['Uming-CN', 'Uming-CN', 'Uming-CN', 'Uming-CN']
}

ALIGNMENTS = {
    'left': TA_LEFT,
    'right': TA_RIGHT,
    'center': TA_CENTER,
    'justified': TA_JUSTIFY
}

AVAILABLE_COLOR_NAMES = {'black', 'red', 'blue', 'green', 'yellow', 'brown', 'cyan', 'gold', 'pink', 'gray', 'white'}
COLORS = {k: getattr(colors, k) for k in AVAILABLE_COLOR_NAMES}
PIXELS_CM = 50
FONT_SIZE_RE = re.compile(r'(\d+)(pt)?')

TplData = namedtuple('TplData', ['width', 'height', 'items', 'background_position', 'width_cm', 'height_cm'])


def _extract_font_size(text):
    return int(FONT_SIZE_RE.match(text).group(1))


class DesignerPDFBase(object):

    def __init__(self, template, config):
        self.config = self._build_config(config)
        self.template = template
        self.tpl_data = self._process_tpl_data(template.data)
        self.page_size = getattr(pagesizes, self.config.page_size.name)
        if self.config.page_orientation == PageOrientation.landscape:
            self.page_size = pagesizes.landscape(self.page_size)
        self.width, self.height = self.page_size
        setTTFonts()

    def _process_tpl_data(self, tpl_data):
        return TplData(width_cm=(float(tpl_data['width']) / PIXELS_CM),
                       height_cm=(float(tpl_data['height']) / PIXELS_CM),
                       **tpl_data)

    def get_pdf(self):
        data = BytesIO()
        canvas = Canvas(data, pagesize=self.page_size)
        self._build_pdf(canvas)
        canvas.save()
        data.seek(0)
        return data

    def _draw_item(self, canvas, item, content, margin_x, margin_y):
        tpl_data = self.tpl_data

        style = ParagraphStyle({})
        style.alignment = ALIGNMENTS[item['text_align']]
        style.textColor = COLORS[item['color']]
        style.fontSize = _extract_font_size(item['font_size'])
        style.leading = style.fontSize

        if item['bold'] and item['italic']:
            style.fontName = FONT_STYLES[item['font_family']][3]
        elif item['italic']:
            style.fontName = FONT_STYLES[item['font_family']][2]
        elif item['bold']:
            style.fontName = FONT_STYLES[item['font_family']][1]
        else:
            style.fontName = FONT_STYLES[item['font_family']][0]

        item_x = float(item['x']) / PIXELS_CM * cm
        item_y = float(item['y']) / PIXELS_CM * cm
        item_width = item['width'] / PIXELS_CM * cm
        item_height = (item['height'] / PIXELS_CM * cm) if item.get('height') is not None else None

        if isinstance(content, Image):
            canvas.drawImage(ImageReader(content), margin_x + item_x, self.height - margin_y - item_height - item_y,
                             item_width, item_height)
        else:
            content = strip_tags(content)
            for line in content.splitlines():
                p = Paragraph(line, style)
                available_height = (tpl_data.height_cm - (item_y / PIXELS_CM)) * cm

                w, h = p.wrap(item_width, available_height)
                if w > item_width or h > available_height:
                    # TODO: add warning
                    pass

                p.drawOn(canvas, margin_x + item_x, self.height - margin_y - item_y - h)
                item_y += h

    def _draw_background(self, canvas, img_reader, pos_x, pos_y, width, height, stretch=True):
        tpl_data = self.tpl_data
        img_width, img_height = img_reader.getSize()

        if stretch:
            bg_x = pos_x
            bg_y = pos_y
            bg_width = width
            bg_height = height
        else:
            bg_width = img_width / tpl_data.pixels_cm * cm
            bg_height = img_height / tpl_data.pixels_cm * cm
            page_width = width
            page_height = height

            bg_x = pos_x + (page_width - bg_width) / 2.0
            bg_y = pos_y + (page_height - bg_height) / 2.0

            if width > page_width:
                ratio = float(page_width) / width
                bg_width = page_width
                bg_height *= ratio
                bg_x = pos_x
                bg_y = pos_y + (page_height - bg_height) / 2.0

            if height > page_height:
                ratio = float(page_height) / height
                bg_height = page_height
                bg_width *= ratio
                bg_x = pos_x + (page_width - bg_width) / 2.0
                bg_y = pos_y

        canvas.drawImage(img_reader, bg_x, bg_y, bg_width, bg_height)

    def _build_config(self, config_data):
        """Build a structured configuration object.

        Should be implemented by inheriting classes
        """
        return NotImplementedError

    def _build_pdf(self, canvas):
        """Generate the actual PDF.

        Should be implemented by inheriting classes.
        """
        raise NotImplementedError
