# -*- coding: utf-8 -*-
##
## $Id: options.py,v 1.1 2009/04/09 13:13:18 dmartinc Exp $
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
    #Collaboration options necessary in all plugins
    ("tab", {"description" : _("Name of tab where the Recording Manager plugin will be placed"),
               "type": str,
               "defaultValue": "Recording Manager",
               "editable": True,
               "visible": True,
               "mustReload": False}),
    ("allowedOn", {"description" : _("Kind of event types (conference, meeting, simple_event) supported"),
               "type": list,
               "defaultValue": ["conference","simple_event","meeting"],
               "editable": True,
               "visible": True,
               "mustReload": False} ),
    ("admins", {"description": _("Recording Request admins / responsibles"),
                      "type": 'users',
                      "defaultValue": [],
                      "editable": True,
                      "visible": True} ),
    #RecordingManager options
    ("sendMailNotifications", {"description" : _("Should mail notifications be sent to responsibles?"),
               "type": bool,
               "defaultValue": False,
               "editable": True,
               "visible": True} ),

    ("micalaDBServer", {"description" : _("Server hosting lecture archiving database"),
               "type": str,
               "defaultValue": "lectureprocessing01.cern.ch",
               "editable": True,
               "visible": True} ),

    ("micalaDBPort", {"description" : _("database port number"),
               "type": str,
               "defaultValue": "3306",
               "editable": True,
               "visible": True} ),

    ("micalaDBName", {"description" : _("Database name"),
               "type": str,
               "defaultValue": "micala",
               "editable": True,
               "visible": True} ),

    ("micalaDBReaderUser", {"description" : _("DB reader account"),
               "type": str,
               "defaultValue": "reader",
               "editable": True,
               "visible": True} ),

    ("micalaDBReaderPW", {"description" : _("DB reader account password"),
               "type": str,
               "defaultValue": "",
               "editable": True,
               "visible": True} ),

    ("micalaDBUser", {"description" : _("DB account for changes"),
               "type": str,
               "defaultValue": "metadata01",
               "editable": True,
               "visible": True} ),

    ("micalaDBPW", {"description" : _("DB account password"),
               "type": str,
               "defaultValue": "",
               "editable": True,
               "visible": True} ),

    ("CDSQueryUrl", {"description" : _("CDS query URL"),
               "type": str,
               "defaultValue": "http://cdsweb.cern.ch/search?p=sysno%%3A%%22INDICO.%s%%22&f=&action_search=Search&sf=&so=d&rm=&rg=1000&sc=1&ot=970&of=t&ap=0",
               "editable": True,
               "visible": True} ),

    ("videoFormatStandard", {"description" : _("Standard video format"),
               "type": str,
               "defaultValue": "720x576 4/3, 25",
               "editable": True,
               "visible": True} ),

    ("videoFormatWide", {"description" : _("Wide-screen video format"),
               "type": str,
               "defaultValue": "720x576 16/9, 25",
               "editable": True,
               "visible": True} ),

    ("contentTypeWebLecture", {"description" : _("Web lecture identifier"),
               "type": str,
               "defaultValue": "WLAPLectureObject-v0.2",
               "editable": True,
               "visible": True} )

]
