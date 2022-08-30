# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from collections import namedtuple
from itertools import product

from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from werkzeug.exceptions import BadRequest

from indico.core import signals
from indico.modules.designer.pdf import DesignerPDFBase
from indico.modules.events.registration.settings import DEFAULT_BADGE_SETTINGS
from indico.util.i18n import _
from indico.util.placeholders import get_placeholders
from indico.util.signals import values_from_signal


FONT_SIZE_RE = re.compile(r'(\d+)(pt)?')
ConfigData = namedtuple('ConfigData', list(DEFAULT_BADGE_SETTINGS))


def _get_font_size(text):
    return int(FONT_SIZE_RE.match(text).group(1))


class RegistrantsListToBadgesPDF(DesignerPDFBase):
    def __init__(self, template, config, event, registrations):
        super().__init__(template, config)
        self.registrations = registrations

    def _build_config(self, config_data):
        return ConfigData(**config_data)

    def _iter_position(self, canvas, n_horizonal, n_vertical):
        """Go over every possible position on the page."""
        config = self.config
        tpl_data = self.tpl_data
        while True:
            for n_x, n_y in product(range(n_horizonal), range(n_vertical)):
                yield (config.left_margin + n_x * (tpl_data.width_cm + config.margin_columns),
                       config.top_margin + n_y * (tpl_data.height_cm + config.margin_rows))
            canvas.showPage()

    def _build_pdf(self, canvas):
        config = self.config

        available_width = self.width - (config.left_margin + config.right_margin + config.margin_columns) * cm
        n_horizontal = int((available_width + config.margin_columns*cm) /
                           ((self.tpl_data.width_cm + config.margin_columns) * cm))
        available_height = self.height - (config.top_margin + config.bottom_margin + config.margin_rows) * cm
        n_vertical = int((available_height + config.margin_rows*cm) /
                         ((self.tpl_data.height_cm + config.margin_rows) * cm))

        if not n_horizontal or not n_vertical:
            raise BadRequest(_('The template dimensions are too large for the page size you selected'))

        # Print a badge for each registration
        for registration, (x, y) in zip(self.registrations, self._iter_position(canvas, n_horizontal, n_vertical)):
            self._draw_badge(canvas, registration, self.template, self.tpl_data, x * cm, y * cm)

    def _draw_badge(self, canvas, registration, template, tpl_data, pos_x, pos_y):
        """
        Draw a badge for a given registration, at position pos_x,
        pos_y (top-left corner).
        """
        config = self.config
        badge_rect = (pos_x, self.height - pos_y - tpl_data.height_cm * cm,
                      tpl_data.width_cm * cm, tpl_data.height_cm * cm)

        if config.dashed_border:
            canvas.saveState()
            canvas.setDash(1, 5)
            canvas.rect(*badge_rect)
            canvas.restoreState()

        if template.background_image:
            with template.background_image.open() as f:
                self._draw_background(canvas, ImageReader(self._remove_transparency(f)), tpl_data, *badge_rect)

        placeholders = get_placeholders('designer-fields')

        # Print images first
        image_placeholders = {name for name, placeholder in placeholders.items() if placeholder.is_image}
        items = sorted(tpl_data.items, key=lambda item: (int(item.get('zIndex', 10)),
                                                         item['type'] not in image_placeholders))

        for item in items:
            placeholder = placeholders.get(item['type'])

            if placeholder:
                if placeholder.group == 'registrant':
                    text = placeholder.render(registration)
                elif placeholder.group == 'event':
                    text = placeholder.render(registration.event)
                elif placeholder.group == 'fixed':
                    text = placeholder.render(item)
                else:
                    raise ValueError(f'Unknown placeholder group: `{placeholder.group}`')
            else:
                continue

            item_data = {'item': item, 'text': text, 'pos_x': pos_x, 'pos_y': pos_y}
            for update in values_from_signal(
                signals.event.designer.draw_item_on_badge.send(registration, items=items, height=self.height,
                                                               width=self.width, data=item_data),
                as_list=True
            ):
                item_data.update(update)
            self._draw_item(canvas, item_data['item'], tpl_data, item_data['text'], item_data['pos_x'],
                            item_data['pos_y'])


class RegistrantsListToBadgesPDFFoldable(RegistrantsListToBadgesPDF):
    def _build_pdf(self, canvas):
        # Only one badge per page
        n_horizontal = 1
        n_vertical = 1

        for registration, (x, y) in zip(self.registrations, self._iter_position(canvas, n_horizontal, n_vertical)):
            self._draw_badge(canvas, registration, self.template, self.tpl_data, x * cm, y * cm)
            if self.tpl_data.width > self.tpl_data.height:
                canvas.translate(self.width, self.height)
                canvas.rotate(180)
                self._draw_badge(canvas, registration, self.template.backside_template, self.backside_tpl_data,
                                 self.width - self.tpl_data.width_cm * cm, y * cm)
                canvas.translate(0, 0)
                canvas.rotate(180)
            else:
                self._draw_badge(canvas, registration, self.template.backside_template, self.backside_tpl_data,
                                 self.tpl_data.width_cm * cm, y * cm)

            tpl_data = self.tpl_data
            canvas.saveState()
            canvas.setDash(1, 5)
            canvas.setStrokeGray(0.5)
            canvas.lines([(tpl_data.width_cm * cm, self.height, tpl_data.width_cm * cm, tpl_data.height_cm * cm),
                          (0, tpl_data.height_cm * cm, self.width, tpl_data.height_cm * cm)])
            canvas.restoreState()


class RegistrantsListToBadgesPDFDoubleSided(RegistrantsListToBadgesPDF):
    def _build_pdf(self, canvas):
        config = self.config

        available_width = self.width - (config.left_margin + config.right_margin + config.margin_columns) * cm
        n_horizontal = int((available_width + config.margin_columns*cm) /
                           ((self.tpl_data.width_cm + config.margin_columns) * cm))
        available_height = self.height - (config.top_margin + config.bottom_margin + config.margin_rows) * cm
        n_vertical = int((available_height + config.margin_rows*cm) /
                         ((self.tpl_data.height_cm + config.margin_rows) * cm))

        if not n_horizontal or not n_vertical:
            raise BadRequest(_('The template dimensions are too large for the page size you selected'))

        per_page = n_horizontal * n_vertical
        # make batch of as many badges as we can fit into one page and add duplicates for printing back sides
        page_used = 0
        badges_mix = []
        for i, reg in enumerate(self.registrations, 1):
            badges_mix.append(reg)
            page_used += 1
            # create another page with the same registrations for the back side
            if (i % per_page) == 0:
                page_used = 0
                badges_mix += badges_mix[-per_page:]

        # if the last page was not full, fill it with blanks and add the back side
        if page_used:
            badges_mix += ([None] * (per_page - page_used)) + badges_mix[-page_used:]

        positioned_badges = zip(badges_mix, self._iter_position(canvas, n_horizontal, n_vertical))
        for i, (registration, (x, y)) in enumerate(positioned_badges):
            if registration is None:
                # blank item for an incomplete last page
                continue
            current_page = (i // per_page) + 1
            # odd pages contain front sides, even pages back sides
            if current_page % 2:
                self._draw_badge(canvas, registration, self.template, self.tpl_data, x * cm, y * cm)
            else:
                # mirror badge coordinates
                x_cm = (self.width - x*cm - self.tpl_data.width_cm*cm)
                self._draw_badge(canvas, registration, self.template.backside_template,
                                 self.backside_tpl_data, x_cm, y * cm)
