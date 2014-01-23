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

globalOptions = [
    #collaboration options necessary in all plugins
    ("tab", {"description" : "Name of tab where CERN MCU will be placed",
               "type": str,
               "defaultValue": "Videoconferencing",
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("allowedOn", {"description" : "Kind of event types (conference, meeting, simple_event) supported",
               "type": list,
               "defaultValue": ["conference", "meeting"],
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("admins", {"description": "CERN MCU admins / responsibles",
                      "type": 'users',
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} ),
    #CERN MCU Options
    ("MCUAddress", {"description": "MCU URL",
                      "type": str,
                      "defaultValue": "https://cern-mcu1.cern.ch",
                      "editable": True,
                      "visible": True}),
    ("indicoID", {"description": "ID of Indico for the MCU",
                      "type": str,
                      "defaultValue": "indico",
                      "editable": True,
                      "visible": True}),
    ("indicoPassword", {"description": "Password of Indico for the MCU",
                      "type": str,
                      "defaultValue": "",
                      "editable": True,
                      "visible": True}),
    ("idRange", {"description": "Range of possible IDs (format: min-max)",
                      "type": str,
                      "defaultValue": "90000-99999",
                      "editable": True,
                      "visible": True}),
    ("MCUTZ", {"description": "Timezone where the MCU is physically located. We assume a MCU Admin will update 'UTC offset' in /settings_time.html of the MCU web interface accordingly.",
                      "type": str,
                      "defaultValue": 'UTC',
                      "editable": True,
                      "visible": True}),
    ("CERNGatekeeperPrefix", {"description": "CERN's gatekeeper prefix. Will be used for instructions on how to join the conference.",
                              "type": str,
                              "defaultValue": "98",
                              "editable": True,
                              "visible": True}),
    ("GDSPrefix", {"description": "GDS prefix. Will be used for instructions on how to join the conference.",
                    "type": str,
                    "defaultValue": "0041227670272",
                    "editable": True,
                    "visible": True}),
    ("MCU_IP", {"description": "MCU's IP. Will be used for instructions on how to join the conference.",
                "type": str,
                "defaultValue": "137.138.145.150",
                "editable": True,
                "visible": True}),
    ("Phone_number", {"description": "Phone number used to join by phone. Will be used for instructions on how to join the conference.",
                              "type": str,
                              "defaultValue": "0041227670270",
                              "editable": True,
                              "visible": True}),
    ("H323_IP_att_name", {"description": "Name of the custom attribute for the H.323 IP of a room in the Room Booking database.",
                              "type": str,
                              "defaultValue": "H323 IP",
                              "editable": True,
                              "visible": True}),

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
]
