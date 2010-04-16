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
    ("tab", {"description" : _("Name of tab where Vidyo will be placed"),
               "type": str,
               "defaultValue": "Videoconferencing",
               "editable": True,
               "visible": True,
               "mustReload": False}),

    ("allowedOn", {"description" : _("Kind of event types (conference, meeting, simple_event) supported"),
               "type": list,
               "defaultValue": ["conference", "meeting", "simple_event"],
               "editable": True,
               "visible": True,
               "mustReload": False}),

    ("admins", {"description": _("Vidyo admins / responsibles"),
                      "type": 'users',
                      "defaultValue": [],
                      "editable": True,
                      "visible": True}),

    #Vidyo Options
    ("sendMailNotifications", {"description" : _("Should mail notifications be sent to Vidyo admins?"),
               "type": bool,
               "defaultValue": False,
               "editable": True,
               "visible": True}),

    ("additionalEmails", {"description": _("Additional email addresses who will receive notifications (always)"),
                          "type": list,
                          "defaultValue": [],
                          "editable": True,
                          "visible": True}),

    ("indicoUsername" , {"description" : _("Indico username for Vidyo"),
                      "type": str,
                      "defaultValue": "indico"}),

    ("indicoPassword" , {"description" : _("Indico password for Vidyo"),
                      "type": str,
                      "defaultValue": ""}),

    ("baseAPILocation", {"description" : _("Vidyo API base URL"),
                         "type": str,
                         "defaultValue": "http://vidyoportal2.cern.ch/services/"}),

    ("adminAPISuffix", {"description" : _("Admin API suffix"),
                         "type": str,
                         "defaultValue": "VidyoPortalAdminService?wsdl"}),

    ("userAPISuffix", {"description" : _("User API suffix"),
                       "type": str,
                       "defaultValue": "VidyoPortalUserService?wsdl"}),

    ("prefix", {"description": _("Prefix for rooms created by Indico"),
                       "type": str,
                       "editable": True,
                       "defaultValue": "9" }),

    ("indicoGroup", {"description": _("Group name for Public Rooms created by Indico"),
                       "type": str,
                       "editable": True,
                       "defaultValue": "Indico" }),

    ('useCERNRBIntegration', {"description": _("Integrate with CERN room booking"),
                       "type": bool,
                       "editable": True,
                       "defaultValue": True }),

    ('CERNRoomGroupName', {"description": _("Group for existing CERN rooms"),
                       "type": str,
                       "editable": True,
                       "defaultValue": "CERN" }),

    ('authenticatorList', {"description": _("Authenticators used to translate Indico user <-> Vidyo account name, by order of preference."),
                       "type": list,
                       "editable": True,
                       "defaultValue": ["Nice", "Local"] }),

    ('sudsCacheLocation', {"description": _("Location of the SOAP client library file cache"),
                       "type": str,
                       "editable": True,
                       "defaultValue": "/tmp/suds/"}),

    ('maxDaysBeforeClean', {"description": _("Number of days after the Indico event's end date after which a public room is considered old."),
                       "type": int,
                       "editable": True,
                       "defaultValue": 7 }),

    ('cleanWarningAmount', {"description": _("Number of public rooms that trigger a mail sent to the admins prompting them to clean the old rooms"),
                       "type": int,
                       "editable": True,
                       "defaultValue": 500 }),

    ('checkTimes', {"description": _("""Times after room should have deleted (for being "old") that we will check if it exists in Vidyo when an user sees it (in hours)"""),
                       "type": list,
                       "editable": True,
                       "defaultValue": [0,12,24,48,96,168,720,1440] })
]
