# -*- coding: utf-8 -*-
##
## $Id: options.py,v 1.2 2009/04/25 13:56:05 dmartinc Exp $
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

globalOptions = [
    #collaboration options necessary in all plugins
    ("subtab", {"description" : "Subtab where EVO will be placed",
               "type": str,
               "defaultValue": "Collaboration",
               "editable": False,
               "visible": False,
               "mustReload": True} ),
    ("allowedOn", {"description" : "Kind of event types (conference, meeting, simple_event) supported",
               "type": list,
               "defaultValue": ["meeting"],
               "editable": False,
               "visible": False,
               "mustReload": True} ),
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
                           "defaultValue": "http://vrvs-contrib.caltech.edu/evoGate/Api/"} ),
    ("expirationTime", {"description" : "Expiration time in minutes",
                           "type": int,
                           "defaultValue": 5} ),
    ("communityList", {"description" : "List of EVO communities",
                      "type": dict,
                      "defaultValue": {},
                      "editable": False} ),
    ("verifyMinutes", {"description" : "Minutes to verify the booking before meeting",
                      "type": list,
                      "defaultValue": [10,30]} ),
    ("allowedMinutes", {"description" : "Temporal margin around Indico event times where we allow EVO meeting creation (minutes)",
                            "type": int,
                            "defaultValue": 60} ),
    ("allowedPastMinutes", {"description" : "Time that we allow EVO meetings to be created in the past (minutes)",
                            "type": int,
                            "defaultValue": 30} ),
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

