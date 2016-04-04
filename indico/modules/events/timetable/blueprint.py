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

from indico.modules.events.timetable.controllers.display import RHTimetable
from indico.modules.events.timetable.controllers.legacy import (RHLegacyTimetableAddContribution,
                                                                RHLegacyTimetableAddBreak,
                                                                RHLegacyTimetableAddSession,
                                                                RHLegacyTimetableAddSessionBlock,
                                                                RHLegacyTimetableGetUnscheduledContributions,
                                                                RHLegacyTimetableScheduleContribution)
from indico.modules.events.timetable.controllers.manage import RHManageTimetable, RHTimetableREST
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('timetable', __name__, template_folder='templates', virtual_template_folder='events/timetable',
                      url_prefix='/event/<confId>')

# Management
_bp.add_url_rule('/manage/timetable/', 'management', RHManageTimetable)
_bp.add_url_rule('/manage/timetable/', 'timetable_rest', RHTimetableREST, methods=('POST',))
_bp.add_url_rule('/manage/timetable/<int:timetable_entry_id>', 'timetable_rest', RHTimetableREST, methods=('PATCH',))

# Timetable legacy operations
_bp.add_url_rule('/manage/timetable/not-scheduled', 'not_scheduled', RHLegacyTimetableGetUnscheduledContributions)
_bp.add_url_rule('/manage/timetable/schedule', 'schedule', RHLegacyTimetableScheduleContribution, methods=('POST',))
_bp.add_url_rule('/manage/timetable/add-break',
                 'add_break', RHLegacyTimetableAddBreak, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/timetable/add-contribution',
                 'add_contribution', RHLegacyTimetableAddContribution, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/timetable/add-session-block',
                 'add_session_block', RHLegacyTimetableAddSessionBlock, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/timetable/add-session', 'add_session', RHLegacyTimetableAddSession, methods=('GET', 'POST'))

# Display
_bp.add_url_rule('/timetable/', 'timetable', RHTimetable)
