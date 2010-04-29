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
    #collaboration options necessary in all plugins
    ("tab", {"description" : _("Name of tab where EVO will be placed"),
               "type": str,
               "defaultValue": "Videoconferencing",
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("allowedOn", {"description" : _("Kind of event types (conference, meeting, simple_event) supported"),
               "type": list,
               "defaultValue": ["meeting"],
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("admins", {"description": _("EVO admins / responsibles"),
                      "type": 'users',
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} ),
    #EVO Options
    ("sendMailNotifications", {"description" : _("Should mail notifications be sent to EVO admins?"),
               "type": bool,
               "defaultValue": False,
               "editable": True,
               "visible": True} ),
    ("additionalEmails", {"description": _("Additional email addresses who will receive notifications (always)"),
                          "type": list,
                          "defaultValue": [],
                          "editable": True,
                          "visible": True} ),
    ("indicoUserID" , {"description" : _("Indico user ID for EVO (right now: integer of max 8 digits)"),
                      "type": str,
                      "defaultValue": ""} ),
    ("indicoPassword" , {"description" : _("Indico password for EVO (right now: integer of 4 digits)"),
                      "type": str,
                      "defaultValue": ""} ),
    ("koalaLocation", {"description" : _("Koala EVO client location"),
                      "type": str,
                      "defaultValue": "http://evo.caltech.edu/evoGate/koala.jnlp"} ),
    ("httpServerLocation", {"description" : _("EVO HTTP server location"),
                           "type": str,
                           "defaultValue": "http://evo.caltech.edu/evoGate/Api/"} ),
    ("expirationTime", {"description" : _("Expiration time in minutes"),
                           "type": int,
                           "defaultValue": 10} ),
    ("communityList", {"description" : _("List of EVO communities"),
                      "type": dict,
                      "defaultValue": {},
                      "editable": False} ),
    ("ingnoredCommunities", {"description" : _("List of EVO communities to be ignored"),
                      "type": dict,
                      "defaultValue": {"1": "EVO Team"},
                      "editable": False,
                      "mustReload" : True} ),
    ("verifyMinutes", {"description" : _("Minutes to verify the booking before meeting"),
                      "type": list,
                      "defaultValue": [10,30]} ),

    ("extraMinutesBefore", {"description" : _("Extra minutes allowed before Indico event start time"),
                            "type": int,
                            "defaultValue": 60} ),
    ("extraMinutesAfter", {"description" : _("Extra minutes allowed after Indico event start time"),
                            "type": int,
                            "defaultValue": 120} ),
    ("defaultMinutesBefore", {"description" : _("Default extra minutes before Indico event start time"),
                            "type": int,
                            "defaultValue": 30} ),
    ("defaultMinutesAfter", {"description" : _("Default extra minutes after Indico event start time"),
                            "type": int,
                            "defaultValue": 60} ),

    ("allowedPastMinutes", {"description" : _("Time that we allow EVO meetings to be created in the past (minutes)"),
                            "type": int,
                            "defaultValue": 30} ),
    ("phoneBridgeNumberList", {"description" : _("Link to list of EVO Phone Bridge numbers"),
                            "type": str,
                            "defaultValue": "http://evo.caltech.edu/evoGate/telephone.jsp"}),

    ("APIMap", {"description" : _("Map of actions and URLs"),
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

