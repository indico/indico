# -*- coding: utf-8 -*-
##
## $Id: options.py,v 1.3 2009/04/25 13:55:51 dmartinc Exp $
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
    ("subtab", {"description" : "Subtab where CERN MCU will be placed",
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
    ("admins", {"description": "CERN MCU admins / responsibles",
                      "type": 'users',
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} ),
    #CERN MCU Options
    ("MCUAddress", {"description": "MCU URL",
                      "type": str,
                      "defaultValue": "http://cern-mcu1.cern.ch",
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
    ("MCU_UTC_offset", {"description": "UTC offset of the MCU. Same value as 'UTC offset' in /settings_time.html of the MCU web interface",
                      "type": int,
                      "defaultValue": 0,
                      "editable": True,
                      "visible": True}),
    ("CERNGatekeeperPrefix", {"description": "CERN's gatekeeper prefix. Will be used for instructions on how to join the conference.",
                              "type": str,
                              "defaultValue": "98",
                              "editable": True,
                              "visible": True}),
    ("GDSPrefix", {"description": "GDS prefix. Will be used for instructions on how to join the conference.",
                    "type": str,
                    "defaultValue": "0041767027098",
                    "editable": True,
                    "visible": True}),
    ("MCU_IP", {"description": "MCU's IP. Will be used for instructions on how to join the conference.",
                "type": str,
                "defaultValue": "137.138.248.216",
                "editable": True,
                "visible": True}),
    ("Phone_number", {"description": "Phone number used to join by phone. Will be used for instructions on how to join the conference.",
                              "type": str,
                              "defaultValue": "0041227670270",
                              "editable": True,
                              "visible": True})
]