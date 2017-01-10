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

from indico.modules.events.timetable.controllers.display import (RHTimetable, RHTimetableEntryInfo,
                                                                 RHTimetableExportPDF, RHTimetableExportDefaultPDF)
from indico.modules.events.timetable.controllers.legacy import (RHLegacyTimetableAddContribution,
                                                                RHLegacyTimetableAddBreak,
                                                                RHLegacyTimetableAddSession,
                                                                RHLegacyTimetableAddSessionBlock,
                                                                RHLegacyTimetableDeleteEntry,
                                                                RHLegacyTimetableGetUnscheduledContributions,
                                                                RHLegacyTimetableScheduleContribution,
                                                                RHLegacyTimetableReschedule,
                                                                RHLegacyTimetableFitBlock, RHLegacyTimetableEditEntry,
                                                                RHLegacyTimetableEditEntryTime,
                                                                RHLegacyTimetableMoveEntry,
                                                                RHLegacyTimetableEditEntryDateTime,
                                                                RHLegacyTimetableShiftEntries,
                                                                RHLegacyTimetableSwapEntries,
                                                                RHLegacyTimetableEditSession,
                                                                RHLegacyTimetableBreakREST)
from indico.modules.events.timetable.controllers.manage import (RHManageTimetable, RHManageSessionTimetable,
                                                                RHTimetableREST, RHManageTimetableEntryInfo)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('timetable', __name__, template_folder='templates', virtual_template_folder='events/timetable',
                      url_prefix='/event/<confId>')

# Management
_bp.add_url_rule('/manage/timetable/', 'management', RHManageTimetable)
_bp.add_url_rule('/manage/timetable/', 'timetable_rest', RHTimetableREST, methods=('POST',))
_bp.add_url_rule('/manage/timetable/<int:entry_id>', 'timetable_rest', RHTimetableREST, methods=('PATCH', 'DELETE'))
_bp.add_url_rule('/manage/timetable/session/<int:session_id>/', 'manage_session', RHManageSessionTimetable)

# Timetable legacy operations
_bp.add_url_rule('/manage/timetable/add-session', 'add_session', RHLegacyTimetableAddSession, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/timetable/break/<int:break_id>', 'legacy_break_rest', RHLegacyTimetableBreakREST,
                 methods=('PATCH',))
with _bp.add_prefixed_rules('/manage/timetable/session/<int:session_id>', '/manage/timetable'):
    _bp.add_url_rule('/', 'session_rest', RHLegacyTimetableEditSession,
                     methods=('PATCH',))
    _bp.add_url_rule('/entry/<int:entry_id>/info', 'entry_info_manage', RHManageTimetableEntryInfo)
    _bp.add_url_rule('/entry/<int:entry_id>/delete', 'delete_entry', RHLegacyTimetableDeleteEntry, methods=('POST',))
    _bp.add_url_rule('/entry/<int:entry_id>/move', 'move_entry', RHLegacyTimetableMoveEntry,
                     methods=('GET', 'POST'))
    _bp.add_url_rule('/entry/<int:entry_id>/shift', 'shift_entries', RHLegacyTimetableShiftEntries, methods=('POST',))
    _bp.add_url_rule('/entry/<int:entry_id>/swap', 'swap_entries', RHLegacyTimetableSwapEntries, methods=('POST',))
    _bp.add_url_rule('/entry/<int:entry_id>/edit/', 'edit_entry', RHLegacyTimetableEditEntry, methods=('GET', 'POST'))
    _bp.add_url_rule('/entry/<int:entry_id>/edit/time', 'edit_entry_time', RHLegacyTimetableEditEntryTime,
                     methods=('GET', 'POST'))
    _bp.add_url_rule('/entry/<int:entry_id>/edit/datetime', 'edit_entry_datetime', RHLegacyTimetableEditEntryDateTime,
                     methods=('POST',))
    _bp.add_url_rule('/block/<block_id>/schedule', 'schedule', RHLegacyTimetableScheduleContribution, methods=('POST',))
    _bp.add_url_rule('/block/<block_id>/fit', 'fit_session_block', RHLegacyTimetableFitBlock, methods=('POST',))
    _bp.add_url_rule('/not-scheduled', 'not_scheduled', RHLegacyTimetableGetUnscheduledContributions)
    _bp.add_url_rule('/schedule', 'schedule', RHLegacyTimetableScheduleContribution, methods=('POST',))
    _bp.add_url_rule('/reschedule', 'reschedule', RHLegacyTimetableReschedule, methods=('POST',))
    _bp.add_url_rule('/add-break', 'add_break', RHLegacyTimetableAddBreak, methods=('GET', 'POST'))
    _bp.add_url_rule('/add-contribution', 'add_contribution', RHLegacyTimetableAddContribution, methods=('GET', 'POST'))
    _bp.add_url_rule('/add-session-block', 'add_session_block', RHLegacyTimetableAddSessionBlock,
                     methods=('GET', 'POST'))

# Display
_bp.add_url_rule('/timetable/', 'timetable', RHTimetable)
_bp.add_url_rule('/timetable/pdf', 'export_pdf', RHTimetableExportPDF, methods=('GET', 'POST'))
_bp.add_url_rule('/timetable/timetable.pdf', 'export_default_pdf', RHTimetableExportDefaultPDF)
_bp.add_url_rule('/timetable/entry/<int:entry_id>/info', 'entry_info', RHTimetableEntryInfo)
