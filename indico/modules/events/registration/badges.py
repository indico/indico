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

from __future__ import unicode_literals, division

import re
from collections import namedtuple
from itertools import izip, product

from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

from indico.modules.designer.pdf import DesignerPDFBase
from indico.modules.events.registration.models.registrations import Registration
from indico.modules.events.registration.settings import DEFAULT_BADGE_SETTINGS
from indico.util.i18n import _
from indico.util.placeholders import get_placeholders


FONT_SIZE_RE = re.compile(r'(\d+)(pt)?')
ConfigData = namedtuple('ConfigData', list(DEFAULT_BADGE_SETTINGS))


def _get_font_size(text):
    return int(FONT_SIZE_RE.match(text).group(1))


class RegistrantsListToBadgesPDF(DesignerPDFBase):

    def __init__(self, template, config, event, registration_ids):
        super(RegistrantsListToBadgesPDF, self).__init__(template, config)
        self.event = event
        self.registrations = (Registration.find(Registration.id.in_(registration_ids), Registration.is_active,
                                                Registration.event_new == event)
                                          .order_by(*Registration.order_by_name).all())

    def _build_config(self, config_data):
        return ConfigData(**config_data)

    def _iter_position(self, canvas, n_horizonal, n_vertical):
        """Go over every possible position on the page."""
        config = self.config
        tpl_data = self.tpl_data
        while True:
            for n_x, n_y in product(xrange(n_horizonal), xrange(n_vertical)):
                yield (config.left_margin + n_x * (tpl_data.width_cm + config.margin_columns),
                       config.top_margin + n_y * (tpl_data.height_cm + config.margin_rows))
            canvas.showPage()

    def _build_pdf(self, canvas):
        config = self.config
        tpl_data = self.tpl_data

        available_width = self.width - (config.left_margin - config.right_margin + config.margin_columns) * cm
        n_horizontal = int(available_width / ((tpl_data.width_cm + config.margin_columns) * cm))
        available_height = self.height - (config.top_margin - config.bottom_margin + config.margin_rows) * cm
        n_vertical = int(available_height / ((tpl_data.height_cm + config.margin_rows) * cm))

        if not (n_horizontal and n_vertical):
            raise ValueError(_("The template dimensions are too large for the page size you selected"))

        # Print a badge for each registration
        for registration, (x, y) in izip(self.registrations, self._iter_position(canvas, n_horizontal, n_vertical)):
            self._draw_badge(canvas, registration, x * cm, y * cm)

    def _draw_badge(self, canvas, registration, pos_x, pos_y):
        """Draw a badge for a given registration, at position pos_x, pos_y (top-left corner)."""
        config = self.config
        tpl_data = self.tpl_data

        badge_rect = (pos_x, self.height - pos_y - tpl_data.height_cm * cm,
                      tpl_data.width_cm * cm, tpl_data.height_cm * cm)

        if config.dashed_border:
            canvas.saveState()
            canvas.setDash(1, 5)
            canvas.rect(*badge_rect)
            canvas.restoreState()

        if self.template.background_image:
            with self.template.background_image.open() as f:
                self._draw_background(canvas, ImageReader(f), *badge_rect)

        placeholders = get_placeholders('designer-fields')

        for item in tpl_data.items:
            placeholder = placeholders.get(item['type'])

            if placeholder:
                if placeholder.group == 'registrant':
                    text = placeholder.render(registration)
                else:
                    text = placeholder.render(registration.event_new)
            elif item['text']:
                text = item['text']

            self._draw_item(canvas, item, text, pos_x, pos_y)
