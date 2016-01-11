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

from MaKaC.webinterface.rh import conferenceModif
from indico.web.flask.blueprints.event.management import event_mgmt


# Timetable
event_mgmt.add_url_rule('/timetable-old/', 'confModifSchedule', conferenceModif.RHConfModifSchedule,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/timetable-old/reschedule', 'confModifSchedule-reschedule', conferenceModif.RHReschedule,
                        methods=('POST',))
event_mgmt.add_url_rule('/timetable-old/dates', 'confModifSchedule-edit', conferenceModif.RHScheduleDataEdit,
                        methods=('GET', 'POST'))

# Session timetable - see the "sessions" module
