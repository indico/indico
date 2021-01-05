# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import re
from collections import namedtuple
from io import BytesIO

from PIL import Image
from reportlab.lib import colors, pagesizes
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph

from indico.legacy.pdfinterface.base import setTTFonts
from indico.modules.designer import PageOrientation
from indico.util.string import strip_tags


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
        self.backside_tpl_data = None
        if template.backside_template:
            self.backside_tpl_data = self._process_tpl_data(template.backside_template.data)
        self.page_size = getattr(pagesizes, self.config.page_size.name)
        if self.config.page_orientation == PageOrientation.landscape:
            self.page_size = pagesizes.landscape(self.page_size)
        self.width, self.height = self.page_size
        setTTFonts()

    def _process_tpl_data(self, tpl_data):
        return TplData(width_cm=(float(tpl_data['width']) / PIXELS_CM),
                       height_cm=(float(tpl_data['height']) / PIXELS_CM),
                       **tpl_data)

    def _remove_transparency(self, fd):
        """Remove transparency from an image and replace it with white."""
        img = Image.open(fd)
        # alpha-channel PNG: replace the transparent areas with plain white
        if img.mode == 'RGBA':
            new = Image.new(img.mode[:-1], img.size, (255, 255, 255))
            new.paste(img, img.split()[-1])
            fd = BytesIO()
            new.save(fd, 'JPEG')
        # XXX: this code does not handle palette (type P) images, such as
        # 8-bit PNGs, but luckily they are somewhat rare nowadays
        fd.seek(0)
        return fd

    def get_pdf(self):
        data = BytesIO()
        canvas = Canvas(data, pagesize=self.page_size)
        self._build_pdf(canvas)
        canvas.save()
        data.seek(0)
        return data

    def _draw_item(self, canvas, item, tpl_data, content, margin_x, margin_y):
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

        if isinstance(content, Image.Image):
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

    def _draw_background(self, canvas, img_reader, tpl_data, pos_x, pos_y, width, height):
        img_width, img_height = img_reader.getSize()

        if tpl_data.background_position == 'stretch':
            bg_x = pos_x
            bg_y = pos_y
            bg_width = width
            bg_height = height
        else:
            bg_width = img_width
            bg_height = img_height
            page_width = width
            page_height = height

            bg_x = pos_x + (page_width - bg_width) / 2.0
            bg_y = pos_y + (page_height - bg_height) / 2.0

            if bg_width > page_width:
                ratio = float(page_width) / bg_width
                bg_width = page_width
                bg_height *= ratio
                bg_x = pos_x
                bg_y = pos_y + (page_height - bg_height) / 2.0

            if bg_height > page_height:
                ratio = float(page_height) / bg_height
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
