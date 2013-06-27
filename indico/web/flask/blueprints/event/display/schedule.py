# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.display import event


# Program
event.add_url_rule('/<confId>/program', 'conferenceProgram', rh_as_view(conferenceDisplay.RHConferenceProgram))
event.add_url_rule('/<confId>/program.pdf', 'conferenceProgram-pdf',
                   rh_as_view(conferenceDisplay.RHConferenceProgramPDF))

# Timetable
event.add_url_rule('/<confId>/timetable/', 'conferenceTimeTable', rh_as_view(conferenceDisplay.RHConferenceTimeTable))
event.add_url_rule('/<confId>/timetable/pdf', 'conferenceTimeTable-customizePdf',
                   rh_as_view(conferenceDisplay.RHTimeTableCustomizePDF))
event.add_url_rule('/<confId>/timetable/timetable.pdf', 'conferenceTimeTable-pdf',
                   rh_as_view(conferenceDisplay.RHTimeTablePDF), methods=('GET', 'POST'))

# Sessions
event.add_url_rule('/<confId>/session/<sessionId>/', 'sessionDisplay', rh_as_view(sessionDisplay.RHSessionDisplay))
event.add_url_rule('/<confId>/session/<sessionId>/session.ics', 'sessionDisplay-ical',
                   rh_as_view(sessionDisplay.RHSessionToiCal))
event.add_url_rule('/<confId>/session/<showSessions>/timetable.pdf', 'conferenceTimeTable-pdf',
                   rh_as_view(conferenceDisplay.RHTimeTablePDF))
