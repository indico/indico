# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.
from MaKaC.i18n import _

globalOptions = [
    ("url", {"description": "Service URL",
             "type": str,
             "defaultValue": "",
             "editable": True,
             "visible": True}),
    ("addToCalendarOperationName", {"description": "Add event operation name",
                                    "type": str,
                                    "defaultValue": 'CreateEventInCalendar',
                                    "editable": True,
                                    "visible": True}),
    ("updateCalendarOperationName", {"description": "Update event operation name",
                                     "type": str,
                                     "defaultValue": 'UpdateExistingEventInCalendar',
                                     "editable": True,
                                     "visible": True}),
    ("removeFromCalendarOperationName", {"description": "Remove event operation name",
                                         "type": str,
                                         "defaultValue": 'DeleteEventInCalendar',
                                         "editable": True,
                                         "visible": True}),
    ("status", {"description": "Default status of the event (free, busy, tentative, oof)",
                "type": str,
                "defaultValue": "free",
                "editable": True,
                "visible": True}),
    ("reminder", {"description": "Turn on calendar reminder",
                  "type": bool,
                  "defaultValue": True,
                  "visible": True}),
    ("reminder_minutes", {"description": "Reminder time (minutes)",
                          "type": int,
                          "defaultValue": "15",
                          "editable": True,
                          "visible": True}),
    ("login", {"description": "Login",
               "type": str,
               "defaultValue": "",
               "editable": True,
               "visible": True}),
    ("password", {"description": "Password",
                  "type": "password",
                  "defaultValue": "",
                  "editable": True,
                  "visible": True}),
    ("prefix", {"description": "Operation ID prefix",
                "type": str,
                "defaultValue": "indico_",
                "editable": True,
                "visible": True}),
    ("timeout", {"description": "Request timeout (seconds)",
                 "type": float,
                 "defaultValue": "2",
                 "editable": True,
                 "visible": True}),
    ("datetimeFormat", {"description": "DateTime format",
                    "type": str,
                    "defaultValue": "MM-dd-yyyy HH:mm",
                    "editable": True,
                    "visible": True}),
]
