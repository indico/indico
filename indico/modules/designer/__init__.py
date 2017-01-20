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

from indico.core.settings import FallbackSettingsProxy
from indico.modules.categories.settings import CategorySettingsProxy
from indico.modules.events.settings import EventSettingsProxy

DEFAULT_BADGE_SETTINGS = {
    'top_margin': 1.6,
    'bottom_margin': 1.1,
    'left_margin': 1.6,
    'right_margin': 1.4,
    'margin_columns': 1.0,
    'margin_rows': 0.0,
    'page_size': 'A4',
    'landscape': False,
    'draw_dashed_rectangles': True
}

event_badge_settings = EventSettingsProxy('badge', DEFAULT_BADGE_SETTINGS)
category_badge_settings = CategorySettingsProxy('badge', DEFAULT_BADGE_SETTINGS)
merged_badge_settings = FallbackSettingsProxy(event_badge_settings, category_badge_settings)
