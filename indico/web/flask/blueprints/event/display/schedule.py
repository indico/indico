# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import conferenceDisplay, sessionDisplay
from indico.web.flask.blueprints.event.display import event


# Program
event.add_url_rule('/program', 'conferenceProgram', conferenceDisplay.RHConferenceProgram)
event.add_url_rule('/program.pdf', 'conferenceProgram-pdf', conferenceDisplay.RHConferenceProgramPDF)

# Timetable
event.add_url_rule('/timetable/', 'conferenceTimeTable', conferenceDisplay.RHConferenceTimeTable)
event.add_url_rule('/timetable/pdf', 'conferenceTimeTable-customizePdf', conferenceDisplay.RHTimeTableCustomizePDF)
event.add_url_rule('/timetable/timetable.pdf', 'conferenceTimeTable-pdf', conferenceDisplay.RHTimeTablePDF,
                   methods=('GET', 'POST'))

# Sessions
event.add_url_rule('/session/<sessionId>/', 'sessionDisplay', sessionDisplay.RHSessionDisplay)
event.add_url_rule('/session/<sessionId>/session.ics', 'sessionDisplay-ical', sessionDisplay.RHSessionToiCal)
event.add_url_rule('/session/<showSessions>/timetable.pdf', 'conferenceTimeTable-pdf', conferenceDisplay.RHTimeTablePDF)
