# -*- coding: utf-8 -*-
##
##
## This file is part of Indico
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN)
##
## Indico is free software: you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico.  If not, see <http://www.gnu.org/licenses/>.
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
