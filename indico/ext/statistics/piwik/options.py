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
    ("jsHookEnabled", {"description": "Enable conference and contribution view tracking",
                  "type": bool,
                  "defaultValue": True,
                  "editable": True,
                  "visible": True}),
    ("downloadTrackingEnabled", {"description": "Enable material download tracking",
                  "type": bool,
                  "defaultValue": True,
                  "editable": True,
                  "visible": True}),
    ("serverUrl", {"description": "Piwik general server URL (piwik.php)",
                  "type": str,
                  "defaultValue": "127.0.0.1/piwik/",
                  "editable": True,
                  "visible": True}),
    ("serverAPIUrl", {"description": "Piwik API server URL (index.php)",
                  "type": str,
                  "defaultValue": "127.0.0.1/piwik/",
                  "editable": True,
                  "visible": True}),
    ("useOnlyServerURL", {"description": "Use only the general URL for all requests",
                  "type": bool,
                  "defaultValue": True,
                  "editable": True,
                  "visible": True}),
    ("serverTok", {"description": "Piwik API token",
                  "type": str,
                  "defaultValue": "",
                  "editable": True,
                  "visible": True}),
    ("serverSiteID", {"description": "Piwik site ID",
                  "type": str,
                  "defaultValue": "1",
                  "editable": True,
                  "visible": True})
]
