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
                      "defaultValue": ""}),
     ("ckEditor" , {"description" : _("Information about how to connect to the chat with a client (Optional)"),
                      "type": 'ckEditor',
                      "defaultValue": "<table width=\"100%\" align=\"center\" border=\"0\">\
    <tr>\
        <td class=\"groupTitle\" style=\"padding-top:50px\"><%= _(\"How to connect to the chat\")%></td>\
    </tr>\
    <tr>\
          <td>\
              <ul>\
                  <li><%= _(\"Download a messaging client compatible with XMPP (like Pidgin, Gajim, Adium, Spark...You may want to look\") %> <a href=http://xmpp.org/software/clients.shtml> <%= _(\"here\") %></a>) <%=_(\"and install it.\")%></li>\
                <li><%= _(\"Add the Jabber account that you want to use.\")%></li>\
                <li><%= _(\"In the menus, try to find something like 'Join a Chat', 'Join Group Chat', or related.\")%></li>\
                <li><%= _(\"Fill the fields Room and Server with the information above. In case there is only one field for both the room and the server, the format to use is 'room@server'.\")%></li>\
            </ul>\
        </td>\
    </tr>\
</table>"}),
]
