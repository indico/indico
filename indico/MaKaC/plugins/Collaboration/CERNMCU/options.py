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
    ("tab", {"description" : _("Name of tab where CERN MCU will be placed"),
               "type": str,
               "defaultValue": "Videoconferencing",
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("allowedOn", {"description" : _("Kind of event types (conference, meeting, simple_event) supported"),
               "type": list,
               "defaultValue": ["conference", "meeting"],
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("admins", {"description": _("CERN MCU admins / responsibles"),
                      "type": 'users',
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} ),
    #CERN MCU Options
    ("MCUAddress", {"description": _("MCU URL"),
                      "type": str,
                      "defaultValue": "https://cern-mcu1.cern.ch",
                      "editable": True,
                      "visible": True}),
    ("indicoID", {"description": _("ID of Indico for the MCU"),
                      "type": str,
                      "defaultValue": "indico",
                      "editable": True,
                      "visible": True}),
    ("indicoPassword", {"description": _("Password of Indico for the MCU"),
                      "type": str,
                      "defaultValue": "",
                      "editable": True,
                      "visible": True}),
    ("idRange", {"description": _("Range of possible IDs (format: min-max)"),
                      "type": str,
                      "defaultValue": "90000-99999",
                      "editable": True,
                      "visible": True}),
    ("MCUTZ", {"description": _("Timezone where the MCU is physically located. We assume a MCU Admin will update 'UTC offset' in /settings_time.html of the MCU web interface accordingly."),
                      "type": str,
                      "defaultValue": 'UTC',
                      "editable": True,
                      "visible": True}),
    ("CERNGatekeeperPrefix", {"description": _("CERN's gatekeeper prefix. Will be used for instructions on how to join the conference."),
                              "type": str,
                              "defaultValue": "98",
                              "editable": True,
                              "visible": True}),
    ("GDSPrefix", {"description": _("GDS prefix. Will be used for instructions on how to join the conference."),
                    "type": str,
                    "defaultValue": "0041227670272",
                    "editable": True,
                    "visible": True}),
    ("MCU_IP", {"description": _("MCU's IP. Will be used for instructions on how to join the conference."),
                "type": str,
                "defaultValue": "137.138.145.150",
                "editable": True,
                "visible": True}),
    ("Phone_number", {"description": _("Phone number used to join by phone. Will be used for instructions on how to join the conference."),
                              "type": str,
                              "defaultValue": "0041227670270",
                              "editable": True,
                              "visible": True}),
    ("H323_IP_att_name", {"description": "Name of the custom attribute for the H.323 IP of a room in the Room Booking database.",
                              "type": str,
                              "defaultValue": "H323 IP",
                              "editable": True,
                              "visible": True}),
]