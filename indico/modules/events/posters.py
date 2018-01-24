# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import division, unicode_literals

from collections import namedtuple

from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

from indico.modules.designer import PageOrientation
from indico.modules.designer.pdf import DesignerPDFBase
from indico.util.placeholders import get_placeholders


ConfigData = namedtuple('ConfigData', ['margin_horizontal', 'margin_vertical', 'page_size', 'page_orientation'])


class PosterPDF(DesignerPDFBase):

    def __init__(self, template, config, event):
        super(PosterPDF, self).__init__(template, config)
        self.event = event

    def _build_config(self, config_data):
        return ConfigData(page_orientation=PageOrientation.portrait, **config_data)

    def _build_pdf(self, canvas):
        config = self.config
        tpl_data = self.tpl_data

        if self.template.background_image:
            with self.template.background_image.open() as f:
                self._draw_background(canvas, ImageReader(self._remove_transparency(f)), tpl_data,
                                      config.margin_horizontal, config.margin_vertical,
                                      tpl_data.width_cm * cm, tpl_data.height_cm * cm)

        placeholders = get_placeholders('designer-fields')

        for item in tpl_data.items:
            placeholder = placeholders.get(item['type'])

            if placeholder:
                if placeholder.group == 'event':
                    text = placeholder.render(self.event)
                else:
                    continue
            elif item.get('text') is not None:
                text = item['text']

            self._draw_item(canvas, item, tpl_data, text, config.margin_horizontal, config.margin_vertical)

    def _draw_poster(self, canvas, registration, pos_x, pos_y):
        """Draw a badge for a given registration, at position pos_x, pos_y (top-left corner).
        """
        config = self.config
        tpl_data = self.tpl_data

        badge_rect = (pos_x, self.height - pos_y - tpl_data.height_cm * cm,
                      tpl_data.width_cm * cm, tpl_data.height_cm * cm)

        if config.dashed_border:
            canvas.saveState()
            canvas.setDash(1, 5)
            canvas.rect(*badge_rect)
            canvas.restoreState()
