# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from indico.core.settings.converters import DatetimeConverter
from indico.modules.events.settings import EventSettingsProxy

paper_reviewing_settings = EventSettingsProxy('paper_reviewing', {
    'start_dt': None,
    'end_dt': None,
    'content_reviewing_enabled': True,
    'layout_reviewing_enabled': False,
    'judge_deadline': None,
    'layout_reviewer_deadline': None,
    'content_reviewer_deadline': None,
}, converters={
    'start_dt': DatetimeConverter,
    'end_dt': DatetimeConverter,
    'judge_deadline': DatetimeConverter,
    'layout_reviewer_deadline': DatetimeConverter,
    'content_reviewer_deadline': DatetimeConverter,
})
