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

from __future__ import unicode_literals

from indico.core.settings.converters import DatetimeConverter, SettingConverter
from indico.modules.events.papers.models.reviews import PaperReviewType
from indico.modules.events.settings import EventSettingsProxy
from indico.util.i18n import _
from indico.util.struct.enum import RichIntEnum


class PaperReviewingRole(RichIntEnum):
    __titles__ = [None, _('Judge'), _('Layout Reviewer'), _('Content Reviewer')]
    __acl_roles__ = [None, 'paper_judge', 'paper_layout_reviewer', 'paper_content_reviewer']
    __review_types__ = [None, None, PaperReviewType.layout, PaperReviewType.content]

    judge = 1
    layout_reviewer = 2
    content_reviewer = 3

    @property
    def acl_role(self):
        return self.__acl_roles__[self]

    @property
    def review_type(self):
        return self.__review_types__[self]


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
    'content_reviewing_enabled': True,
    'layout_reviewing_enabled': False,
    'judge_deadline': None,
    'layout_reviewer_deadline': None,
    'content_reviewer_deadline': None,
    'enforce_judge_deadline': False,
    'enforce_layout_reviewer_deadline': False,
    'enforce_content_reviewer_deadline': False,
    'announcement': '',
    'scale_lower': -3,
    'scale_upper': 3,

    # Notifications
    'notify_on_added_to_event': set(),
    'notify_on_assigned_contrib': set(),
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
