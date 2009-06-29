# -*- coding: utf-8 -*-
##
## $Id: options.py,v 1.1 2009/04/09 13:13:18 dmartinc Exp $
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
    ("subtab", {"description" : "Subtab where the Recording Request plugin will be placed",
               "type": str,
               "defaultValue": "Recording Request",
               "editable": False,
               "visible": False,
               "mustReload": True}),
    ("allowedOn", {"description" : "Kind of event types (conference, meeting, simple_event) supported",
               "type": list,
               "defaultValue": ["conference","simple_event","meeting"],
               "editable": False,
               "visible": False,
               "mustReload": True} ),
    ("admins", {"description": "Recording Request admins / responsibles",
                      "type": 'users',
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} ),
    #RecordingRequest options
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
    
    ("contributionWarnLimit", {"description" : "Allowed number of loaded contributions without warning",
               "type": int,
               "defaultValue": 20,
               "editable": True,
               "visible": True} ),
               
    ("ConsentFormURL", {"description" : "Recording consent form URL",
               "type": str,
               "defaultValue": "",
               "editable": True,
               "visible": True})
]