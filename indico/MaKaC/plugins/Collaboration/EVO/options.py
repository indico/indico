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
    #collaboration options necessary in all plugins
    ("tab", {"description" : "Name of tab where EVO will be placed",
               "type": str,
               "defaultValue": "Videoconferencing",
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("allowedOn", {"description" : "Kind of event types (conference, meeting, simple_event) supported",
               "type": list,
               "defaultValue": ["meeting"],
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("admins", {"description": "EVO admins / responsibles",
                      "type": 'users',
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} ),
    #EVO Options
    ("sendMailNotifications", {"description" : "Should mail notifications be sent to EVO admins?",
               "type": bool,
               "defaultValue": False,
               "editable": True,
               "visible": True} ),
    ("additionalEmails", {"description": "Additional email addresses who will receive notifications (always)",
                          "type": list,
                          "defaultValue": [],
                          "editable": True,
                          "visible": True} ),
    ("indicoUserID" , {"description" : "Indico user ID for EVO (right now: integer of max 8 digits)",
                      "type": str,
                      "defaultValue": ""} ),
    ("indicoPassword" , {"description" : "Indico password for EVO (right now: integer of 4 digits)",
                      "type": str,
                      "defaultValue": ""} ),
    ("koalaLocation", {"description" : "Koala EVO client location",
                      "type": str,
                      "defaultValue": "http://evo.caltech.edu/evoGate/koala.jnlp"} ),
    ("httpServerLocation", {"description" : "EVO HTTP server location",
                           "type": str,
                           "defaultValue": "http://evo.caltech.edu/evoGate/Api/"} ),
    ("expirationTime", {"description" : "Expiration time in minutes",
                           "type": int,
                           "defaultValue": 10} ),
    ("communityList", {"description" : "List of EVO communities",
                      "type": dict,
                      "defaultValue": {},
                      "editable": False} ),
    ("ingnoredCommunities", {"description" : "List of EVO communities to be ignored",
                      "type": dict,
                      "defaultValue": {"1": "EVO Team"},
                      "editable": False,
                      "mustReload" : True} ),
    ("verifyMinutes", {"description" : "Minutes to verify the booking before meeting",
                      "type": list,
                      "defaultValue": [10,30]} ),

    ("extraMinutesBefore", {"description" : "Extra minutes allowed before Indico event start time",
                            "type": int,
                            "defaultValue": 60} ),
    ("extraMinutesAfter", {"description" : "Extra minutes allowed after Indico event start time",
                            "type": int,
                            "defaultValue": 120} ),
    ("defaultMinutesBefore", {"description" : "Default extra minutes before Indico event start time",
                            "type": int,
                            "defaultValue": 30} ),
    ("defaultMinutesAfter", {"description" : "Default extra minutes after Indico event start time",
                            "type": int,
                            "defaultValue": 60} ),

    ("allowedPastMinutes", {"description" : "Time that we allow EVO meetings to be created in the past (minutes)",
                            "type": int,
                            "defaultValue": 30} ),
    ("phoneBridgeNumberList", {"description" : "Link to list of EVO Phone Bridge numbers",
                            "type": str,
                            "defaultValue": "http://evo.caltech.edu/evoGate/telephone.jsp"}),

    ("APIMap", {"description" : "Map of actions and URLs",
               "type": dict,
               "defaultValue": {
                                "reloadCommunityList" : "communities.jsp",
                                "create" : "create.jsp",
                                "modify" : "modify.jsp",
                                "delete" : "delete.jsp",
                                "getInfo": "meeting.jsp"
                               },
               "editable": False,
               "visible": False,
               "mustReload": True} )

]

