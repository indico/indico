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

from indico.core.settings.converters import DatetimeConverter, SettingConverter
from indico.modules.events.settings import EventSettingsProxy
from indico.util.struct.enum import IndicoEnum


class PaperReviewingRole(int, IndicoEnum):
    judge = 1
    layout_reviewer = 2
    content_reviewer = 3


class RoleConverter(SettingConverter):
    @staticmethod
    def from_python(value):
        return [v.name for v in value]

    @staticmethod
    def to_python(value):
        return {PaperReviewingRole.get(v) for v in value}


paper_reviewing_settings = EventSettingsProxy('paper_reviewing', {
    'start_dt': None,
    'end_dt': None,
    'enforce_deadlines': False,
    'content_reviewing_enabled': True,
    'layout_reviewing_enabled': False,
    'judge_deadline': None,
    'layout_reviewer_deadline': None,
    'content_reviewer_deadline': None,

    # Notifications
    'notify_on_added_to_event': {},
    'notify_on_assigned_contrib': {},
    'notify_on_paper_submission': {PaperReviewingRole.layout_reviewer, PaperReviewingRole.content_reviewer},
    'notify_judge_on_review': True,
    'notify_author_on_judgment': True
}, converters={
    'start_dt': DatetimeConverter,
    'end_dt': DatetimeConverter,
    'judge_deadline': DatetimeConverter,
    'layout_reviewer_deadline': DatetimeConverter,
    'content_reviewer_deadline': DatetimeConverter,
    'notify_on_added_to_event': RoleConverter,
    'notify_on_assigned_contrib': RoleConverter,
    'notify_on_paper_submission': RoleConverter
})
