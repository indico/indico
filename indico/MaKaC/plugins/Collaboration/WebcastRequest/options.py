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
    ("ElectronicAgreementTab", {"description": "Name of tab where the Electronic Agreement will be placed",
               "defaultValue": "Electronic Agreement",
               "type": str,
               "editable": False
               }),
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

    ("ConsentFormURL", {"description" : "Link to the paper agreement",
               "type": str,
               "defaultValue": "",
               "editable": True,
               "visible": True}),

    ("AgreementName", {"description" : "Agreement name",
               "type": str,
               "defaultValue": "agreement",
               "editable": True,
               "visible": True}),

    ("AgreementNotificationURL", {"description" : "URL to send agreement notification to",
               "type": str,
               "defaultValue": "",
               "editable": True,
               "visible": True}),

    ("webcastCapableRooms", {"description": "Rooms capable of webcasting",
                      "type": "rooms",
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} ),

    # Audience-related options
    ("webcastPublicURL", {"description" : "Webcast service URL (for default 'Public' audience)",
               "type": str,
               "defaultValue": "",
               "editable": True,
               "visible": True}),

    ("webcastAudiences", {"description": "Private webcast audiences/service URLs",
                      "type": "links",
                      "subType": "webcastAudiences",
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} )
]
