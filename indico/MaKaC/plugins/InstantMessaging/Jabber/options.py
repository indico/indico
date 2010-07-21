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
    ("chatServerHost", {"description": _("Hostname of the chat server"),
                          "type": str,
                          "defaultValue": "jabber.cern.ch",
                          "editable": True,
                          "visible": True} ),

    ("admins", {"description": _("Jabber admins / responsibles"),
               "type": 'users',
               "defaultValue": [],
               "editable": True,
               "visible": True}),

    ("sendMailNotifications", {"description" : _("Should mail notifications be sent to Jabber admins?"),
               "type": bool,
               "defaultValue": False,
               "editable": True,
               "visible": True}),

    ("additionalEmails", {"description": _("Additional email addresses who will receive notifications (always)"),
                          "type": list,
                          "defaultValue": [],
                          "editable": True,}),

    ("indicoUsername" , {"description" : _("Indico username for Jabber"),
                      "type": str,
                      "defaultValue": "indico"}),

    ("indicoPassword" , {"description" : _("Indico password for Jabber"),
                      "type": 'password',
                      "defaultValue": ""})
]
