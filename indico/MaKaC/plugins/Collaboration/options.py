# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
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


def foo():
    return 'aa'