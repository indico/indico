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
## along with Indico;if not, see <http://www.gnu.org/licenses/>.
from MaKaC.i18n import _


globalOptions = [
    ("collaborationAdmins", {"description": "Global collaboration admins",
                            "type": 'users',
                            "defaultValue": []} ),
    ("sendMailNotifications", {"description" : "Should mail notifications be sent to Collaborations admins?",
               "type": bool,
               "defaultValue": False,
               "editable": True,
               "visible": True} ),
    ("additionalEmails", {"description": "Additional email addresses who will receive notifications (always)",
                          "type": list,
                          "defaultValue": [],
                          "editable": True,
                          "visible": True} ),
    ("tabOrder", {"description": "Order in which the tabs will appear",
                  "type": list,
                  "defaultValue": ["Videoconferencing", "Recording Request", "Webcast Request"]
                  }),
    ("ravemAPIURL", {"description" : "RAVEM API server",
                       "type": str,
                       "defaultValue": "http://ravem.cern.ch//api/services/"}),
    ("ravemUsername" , {"description" : "Username for RAVEM API",
                      "type": str,
                      "defaultValue": "ravem"}),
    ("ravemPassword" , {"description" : "Password for RAVEM API",
                      "type": str,
                      "defaultValue": ""}),
    ("pluginsPerEventType", {"description": "Plugins allowed for each event type",
                            "type": dict, #key: a string: conference, simple_event or meeting. Value: list of Plugin objects
                            "editable": False,
                            "visible": True} ),
    ("pluginsPerIndex", {"description": "Information about each index seen by collaboration admins",
                         "type": list, #a list of IndexInformation objects
                         "editable": False,
                         "visible": True} ),
    ("verifyIndexingResults", {"description": """Verify that indexing results do not contain bookings from plugins that have been removed in order to avoid exceptions (not efficient)""",
                         "type": bool,
                         "defaultValue": False})
]
