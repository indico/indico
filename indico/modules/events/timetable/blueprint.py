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

from indico.modules.events.timetable.controllers import (RHManageTimetable, RHTimetableREST, RHTimetable,
                                                         RHManageTimetableGetUnscheduledContributions,
                                                         RHManageTimetableScheduleContribution)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('timetable', __name__, template_folder='templates', virtual_template_folder='events/timetable',
                      url_prefix='/event/<confId>')

# Management
_bp.add_url_rule('/manage/timetable/', 'management', RHManageTimetable)
_bp.add_url_rule('/manage/timetable/', 'timetable_rest', RHTimetableREST, methods=('POST',))
_bp.add_url_rule('/manage/timetable/<int:timetable_entry_id>', 'timetable_rest', RHTimetableREST, methods=('PATCH',))

# Timetable management operations
_bp.add_url_rule('/manage/timetable/not-scheduled', 'not_scheduled', RHManageTimetableGetUnscheduledContributions)
_bp.add_url_rule('/manage/timetable/schedule', 'schedule', RHManageTimetableScheduleContribution, methods=('POST',))

# Display
_bp.add_url_rule('/timetable/', 'timetable', RHTimetable)
