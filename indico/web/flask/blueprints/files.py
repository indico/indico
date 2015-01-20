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
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import materialDisplay, fileAccess
from indico.web.flask.wrappers import IndicoBlueprint


files = IndicoBlueprint('files', __name__)

# Material (event)
files.add_url_rule('/event/<confId>/material/<materialId>/', 'materialDisplay', materialDisplay.RHMaterialDisplay)
files.add_url_rule('/event/<confId>/contribution/<contribId>/material/<materialId>/', 'materialDisplay',
                   materialDisplay.RHMaterialDisplay)
files.add_url_rule('/event/<confId>/session/<sessionId>/contribution/<contribId>/material/<materialId>/',
                   'materialDisplay', materialDisplay.RHMaterialDisplay)
files.add_url_rule('/event/<confId>/material/<materialId>/accesskey', 'materialDisplay-accessKey',
                   materialDisplay.RHMaterialDisplayStoreAccessKey, methods=('POST',))

# Material (category)
files.add_url_rule('/category/<categId>/material/<materialId>/', 'materialDisplay', materialDisplay.RHMaterialDisplay)
files.add_url_rule('/category/<categId>/material/<materialId>/accesskey', 'materialDisplay-accessKey',
                   materialDisplay.RHMaterialDisplayStoreAccessKey, methods=('POST',))

# File access (event)
files.add_url_rule(
    '/event/<confId>/session/<sessionId>/material/<materialId>/<resId>.<fileExt>', 'getFile-access',
    fileAccess.RHFileAccess)
files.add_url_rule(
    '/event/<confId>/session/<sessionId>/material/<materialId>/<resId>', 'getFile-access', fileAccess.RHFileAccess)
files.add_url_rule(
    '/event/<confId>/session/<sessionId>/contribution/<contribId>/material/<materialId>/<resId>.<fileExt>',
    'getFile-access', fileAccess.RHFileAccess)
files.add_url_rule(
    '/event/<confId>/session/<sessionId>/contribution/<contribId>/<subContId>/material/<materialId>/<resId>.<fileExt>',
    'getFile-access', fileAccess.RHFileAccess)
files.add_url_rule('/event/<confId>/contribution/<contribId>/material/<materialId>/<resId>.<fileExt>', 'getFile-access',
                   fileAccess.RHFileAccess)
files.add_url_rule('/event/<confId>/contribution/<contribId>/<subContId>/material/<materialId>/<resId>.<fileExt>',
                   'getFile-access', fileAccess.RHFileAccess)
files.add_url_rule('/event/<confId>/material/<materialId>/<resId>.<fileExt>', 'getFile-access', fileAccess.RHFileAccess)
files.add_url_rule('/event/<confId>/registration/attachments/<registrantId>-<resId>.<fileExt>', 'getFile-access',
                   fileAccess.RHFileAccess)
files.add_url_rule('/event/<confId>/material/<materialId>/<resId>', 'getFile-access', fileAccess.RHFileAccess)


# File access (category)
files.add_url_rule('/category/<categId>/material/<materialId>/<resId>.<fileExt>', 'getFile-access',
                   fileAccess.RHFileAccess)
files.add_url_rule('/category/<categId>/material/<materialId>/<resId>', 'getFile-access', fileAccess.RHFileAccess)

# File access (generic)
files.add_url_rule('/file/video.swf', 'getFile-flash', fileAccess.RHVideoFlashAccess)
files.add_url_rule('/file/video.wmv', 'getFile-wmv', fileAccess.RHVideoWmvAccess)
files.add_url_rule('/file/accesskey', 'getFile-accessKey', fileAccess.RHFileAccessStoreAccessKey, methods=('POST',))
