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
    ("tab", {"description" : "Name of tab where Vidyo will be placed",
               "type": str,
               "defaultValue": "Videoconferencing",
               "editable": True,
               "visible": True,
               "mustReload": False}),

    ("allowedOn", {"description" : "Kind of event types (conference, meeting, simple_event) supported",
               "type": list,
               "defaultValue": ["conference", "meeting", "simple_event"],
               "editable": True,
               "visible": True,
               "mustReload": False}),

    ("admins", {"description": "Vidyo admins / responsibles",
                      "type": 'users',
                      "defaultValue": [],
                      "editable": True,
                      "visible": True}),

    ( "AuthorisedUsersGroups", {"description": "Users and Groups authorised to create Vidyo bookings",
                                "type": 'usersGroups',
                                "defaultValue": [],
                                "editable": True,
                                "visible": True}),

    #Vidyo Options

    ("sendMailNotifications", {"description" : "Should mail notifications be sent to Vidyo admins?",
               "type": bool,
               "defaultValue": False,
               "editable": True,
               "visible": True}),

    ("contactSupport" , {"description" : "Vidyo email support",
                      "type": str,
                      "defaultValue": ""}),

    ("additionalEmails", {"description": "Additional email addresses who will receive notifications (always)",
                          "type": list,
                          "defaultValue": [],
                          "editable": True,
                          "visible": True}),

    ("indicoUsername" , {"description" : "Indico username for Vidyo",
                      "type": str,
                      "defaultValue": "indico"}),

    ("indicoPassword" , {"description" : "Indico password for Vidyo",
                      "type": str,
                      "defaultValue": ""}),

    ("baseAPILocation", {"description" : "Vidyo API base URL",
                         "type": str,
                         "defaultValue": "http://vidyoportal2.cern.ch/services/"}),

    ("adminAPIURL", {"description" : "Admin API WSDL URL",
                         "type": str,
                         "defaultValue": "http://vidyoportal2.cern.ch/services/VidyoPortalAdminService?wsdl"}),

    ("userAPIURL", {"description" : "User API WSDL URL",
                       "type": str,
                       "defaultValue": "http://vidyoportal2.cern.ch/services/VidyoPortalUserService?wsdl"}),

    ("prefix", {"description": "Prefix for rooms created by Indico",
                       "type": str,
                       "editable": True,
                       "defaultValue": "9" }),

    ("prefixConnect", {"description": "Prefix to use when connecting a CERN capable room to a Vidyo room",
                       "type": str,
                       "editable": True,
                       "defaultValue": "21" }),

    ("indicoGroup", {"description": "Group name for Public Rooms created by Indico",
                       "type": str,
                       "editable": True,
                       "defaultValue": "Indico" }),

    ('useCERNRBIntegration', {"description": "Integrate with CERN room booking",
                       "type": bool,
                       "editable": True,
                       "defaultValue": True }),

    ('CERNRoomGroupName', {"description": "Group for existing CERN rooms",
                       "type": str,
                       "editable": True,
                       "defaultValue": "CERN" }),

    ('authenticatorList', {"description": "Authenticators used to translate Indico user <-> Vidyo account name, by order of preference.",
                       "type": list,
                       "editable": True,
                       "defaultValue": ["Nice", "Local"] }),

    ('sudsCacheLocation', {"description": "Location of the SOAP client library file cache",
                       "type": str,
                       "editable": True,
                       "defaultValue": "/tmp/suds/"}),

    ('maxDaysBeforeClean', {"description": "Number of days after the Indico event's end date after which a public room is considered old.",
                       "type": int,
                       "editable": True,
                       "defaultValue": 7 }),

    ('cleanWarningAmount', {"description": "Number of public rooms that trigger a mail sent to the admins prompting them to clean the old rooms",
                       "type": int,
                       "editable": True,
                       "defaultValue": 500 }),

    ('phoneNumbers', {"description": "VidyoVoice Phone Numbers",
                       "type": "list_multiline",
                       "editable": True,
                       "defaultValue": [] })
]
