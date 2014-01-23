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

_emailReplacerNote = """
You can use the following placeholders:<br />{bookedForUser}, {roomName}, {roomAtts[ATTNAME]}, {bookingStart}, {bookingEnd}, {occStart}, {occEnd}, {detailsLink}
""".strip()

_emailSubjectReplacerNote = """
You can use the following placeholders:<br />{roomName}, {roomAtts[ATTNAME]}, {bookingStart}, {bookingEnd}, {occStart}, {occEnd}
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
        "description": "Should bookings require an existing user in the 'booked for' field",
        "type" : bool,
        "defaultValue": False}),
    ("notificationEmails", {
        "description": "Email addresses which will receive booking start/end notifications",
        "type": list,
        "defaultValue": [],
        "editable": True,
        "visible": True}),
    ("assistanceNotificationEmails", {
        "description": "Email to which the conference rooms technical support requests are sent",
        "type": list,
        "defaultValue": [],
        "editable": True,
        "visible": True}),
    ("notificationEmailsToBookedFor", {
        "description": "Should the emails listed in 'booked for' also receive notification emails",
        "type" : bool,
        "defaultValue": False}),
    ("startNotificationEmailSubject", {
        "description": "Email subject when a booking starts",
        "type" : str,
        "defaultValue": '',
        "note": _emailSubjectReplacerNote}),
    ("startNotificationEmail", {
        "description": "Email to send when a booking starts",
        "type" : 'textarea',
        "defaultValue": '',
        "note": _emailReplacerNote}),
    ("endNotificationEmailSubject", {
        "description": "Email subject when a booking ends",
        "type" : str,
        "defaultValue": '',
        "note": _emailSubjectReplacerNote}),
    ("endNotificationEmail", {
        "description": "Email to send when a booking ends",
        "type" : 'textarea',
        "defaultValue": '',
        "note": _emailReplacerNote}),
    ("notificationHour", {"description" : "Hour at which the start notifications should be sent (0-23)",
                            "type": int,
                            "defaultValue": 6}),
    ("notificationBefore", {"description" : "Trigger start notifications X days before the booking (occurrence) starts.",
                            "type": int,
                            "defaultValue": 0})

]
