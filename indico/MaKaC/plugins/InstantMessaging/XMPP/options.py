# -*- coding: utf-8 -*-
##
## $Id: options.py,v 1.2 2009/04/25 13:56:05 dmartinc Exp $
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
    ("chatServerHost", {"description": "Hostname of the chat server",
                        "type": str,
                        "defaultValue": "",
                        "editable": True,
                        "visible": True} ),

    ("admins", {"description": "XMPP admins / responsibles",
                "type": 'users',
                "defaultValue": [],
                "editable": True,
                "visible": True}),

    ("sendMailNotifications", {"description" : "Should mail notifications be sent to XMPP admins?",
                               "type": bool,
                               "defaultValue": False,
                               "editable": True,
                               "visible": True}),

    ("additionalEmails", {"description": "Additional email addresses who will receive notifications (always)",
                          "type": list,
                          "defaultValue": [],
                          "editable": True,}),

    ("indicoUsername" , {"description" : "Indico username for XMPP",
                         "type": str,
                         "defaultValue": "indico"}),

    ("indicoPassword" , {"description" : "Indico password for XMPP",
                      "type": 'password',
                      "defaultValue": ""}),
     ("ckEditor" , {"description" : "Information about how to connect to the chat with a client (Optional)",
                      "type": 'ckEditor',
                      "defaultValue": "<table width=\"100%\" align=\"center\" border=\"0\">\
    <tr>\
        <td class=\"groupTitle\">How to connect to the chat</td>\
    </tr>\
    <tr>\
          <td>\
              <ul>\
                  <li>Download a messaging client compatible with XMPP (like Pidgin, Gajim, Adium, Spark...You may want to look <a href=http://xmpp.org/software/clients.shtml> here</a>) and install it.</li>\
                <li>Add the XMPP account that you want to use.</li>\
                <li>In the menus, try to find something like 'Join a Chat', 'Join Group Chat', or related.</li>\
                <li>Fill the fields Room and Server with the information above. In case there is only one field for both the room and the server, the format to use is 'room@server'.</li>\
            </ul>\
        </td>\
    </tr>\
</table>"}),

    ("activateLogs", {"description": """Make possible to see chat logs and attach them to the material <div style="font-style: italic; margin-top:5px;">You will need to configure a web service in your XMPP server - see <a href="">here</a>.</div>""",
                            "type": bool,
                            "defaultValue": False,
                            "editable": True,
                            "visible": True})
#    ("joinWebClient", {"description": "Show a link to join a chat room through our web client",
#                            "type": bool,
#                            "defaultValue": True,
#                            "editable": True,
#                            "visible": True})
]
