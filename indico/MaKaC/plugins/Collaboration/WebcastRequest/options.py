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

globalOptions = [
    #Collaboration options necessary in all plugins
    ("tab", {"description" : "Tab where the Webcast Request plugin will be placed",
               "type": str,
               "defaultValue": "Webcast Request",
               "editable": True,
               "visible": True,
               "mustReload": False}),
    ("allowedOn", {"description" : "Kind of event types (conference, meeting, simple_event) supported",
               "type": list,
               "defaultValue": ["conference","simple_event","meeting"],
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("admins", {"description": "Webcast Request admins / responsibles",
                      "type": "users",
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} ),
    #WebcastRequest options
    ("sendMailNotifications", {"description" : "Should mail notifications be sent to responsibles?",
               "type": bool,
               "defaultValue": False,
               "editable": True,
               "visible": True} ),
    ("additionalEmails", {"description": "Additional email addresses who will receive notifications (always)",
                          "type": list,
                          "defaultValue": [],
                          "editable": True,
                          "visible": True} ),
    
    ("contributionLoadLimit", {"description" : "Allowed number of talks fetched on new request page load",
               "type": int,
               "defaultValue": 20,
               "editable": True,
               "visible": True} ),
               
    ("ConsentFormURL", {"description" : "Webcast consent form URL",
               "type": str,
               "defaultValue": "",
               "editable": True,
               "visible": True}),
               
    ("webcastCapableRooms", {"description": "Rooms capable of webcasting",
                      "type": "rooms",
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} )
]