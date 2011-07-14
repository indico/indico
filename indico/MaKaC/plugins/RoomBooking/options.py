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

_emailReplacerNote = """
You can use the following placeholders:<br />{bookedForUser}, {roomName}, {roomAtts[ATTNAME]}, {bookingStart}, {bookingEnd}, {detailsLink}
""".strip()

_emailSubjectReplacerNote = """
You can use the following placeholders:<br />{roomName}, {roomAtts[ATTNAME]}, {bookingStart}, {bookingEnd}
""".strip()

globalOptions = [
    ( "Managers", {"description": "Users and Groups authorised to administrate/manage the roombooking module (create/delete/edit all rooms/bookings)",
                                  "type": 'usersGroups',
                                  "defaultValue": [],
                                  "editable": True,
                                  "visible": True}),
    ( "AuthorisedUsersGroups", {"description": "Users and Groups authorised to access roombooking interface",
                                "type": 'usersGroups',
                                "defaultValue": [],
                                "editable": True,
                                "visible": True}),
    ("bookingsForRealUsers", {
        "description": _("Should bookings require an existing user in the 'booked for' field"),
        "type" : bool,
        "defaultValue": False}),
    ("notificationEnabled", {
        "description": _("Enable the tasks for booking start/end notification. Only bookings created/modified after enabling it will trigger notifications"),
        "type" : bool,
        "defaultValue": False}),
    ("notificationEmails", {
        "description": _("Email addresses which will receive booking start/end notifications"),
        "type": list,
        "defaultValue": [],
        "editable": True,
        "visible": True}),
    ("notificationEmailsToBookedFor", {
        "description": _("Should the emails listed in 'booked for' also receive notification emails"),
        "type" : bool,
        "defaultValue": False}),
    ("startNotificationEmailSubject", {
        "description": _("Email subject when a booking starts"),
        "type" : str,
        "defaultValue": '',
        "note": _emailSubjectReplacerNote}),
    ("startNotificationEmail", {
        "description": _("Email to send when a booking starts"),
        "type" : 'textarea',
        "defaultValue": '',
        "note": _emailReplacerNote}),
    ("endNotificationEmailSubject", {
        "description": _("Email subject when a booking ends"),
        "type" : str,
        "defaultValue": '',
        "note": _emailSubjectReplacerNote}),
    ("endNotificationEmail", {
        "description": _("Email to send when a booking ends"),
        "type" : 'textarea',
        "defaultValue": '',
        "note": _emailReplacerNote}),
    ("notificationBefore", {"description" : _("Trigger start notifications X minutes before the booking starts. Changes will not affect existing bookings"),
                           "type": int,
                           "defaultValue": 0} )]
