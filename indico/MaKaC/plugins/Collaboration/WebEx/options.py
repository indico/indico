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
from MaKaC.i18n import _

globalOptions = [
    #collaboration options necessary in all plugins
    ("tab", {"description" : "Name of tab where WebEx will be placed",
               "type": str,
               "defaultValue": "Videoconferencing",
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("allowedOn", {"description" : "Kind of event types (conference, meeting, simple_event) supported",
               "type": list,
               "defaultValue": ["meeting", "conference", "simple_event"],
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("admins", {"description": "WebEx admins / responsibles",
               "type": 'users',
               "defaultValue": [],
               "editable": True,
               "visible": True} ),
    ("AuthorizedUsersGroups", {"description": "Users and Groups authorized to create WebEx bookings",
               "type": 'usersGroups',
               "defaultValue": [],
               "editable": True,
               "visible": True}),
    #WebEx Options
    ("sendMailNotifications", {"description" : "Should mail notifications be sent to WebEx admins?",
               "type": bool,
               "defaultValue": False,
               "editable": True,
               "visible": True} ),
    ("additionalEmails", {"description": "Additional email addresses who will receive notifications (always)",
               "type": list,
               "defaultValue": [],
               "editable": True,
               "visible": True}),
    ("WESiteID" , {"description" : "WebEx site ID",
               "type": str,
               "defaultValue": ""} ),
    ("WEPartnerID" , {"description" : "WebEx partner ID",
               "type": str,
               "defaultValue": ""} ),
    ("WEhttpServerLocation", {"description" : "WebEx HTTP server location",
               "type": str,
               "defaultValue": ""} ),
    ("verifyMinutes", {"description" : "Minutes to verify the booking before meeting",
               "type": list,
               "defaultValue": [10,30]} ),
    ("allowedMinutes", {"description" : "Temporal margin around the Indico event times we allow WebEx meeting creation (minutes)",
               "type": int,
               "defaultValue": 60} ),
    ("allowedPastMinutes", {"description" : "Time that we allow WebEx meetings to be created in the past (minutes)",
               "type": int,
               "defaultValue": 30} )

]

