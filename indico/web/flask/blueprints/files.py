# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh.fileAccess import RHFileAccess
from indico.web.flask.wrappers import IndicoBlueprint


files = IndicoBlueprint('files', __name__)

# TODO: Remove when reviewing is rewritten.
files.add_url_rule(
    '/event/<confId>/session/<sessionId>/contribution/<contribId>/material-old/<materialId>/<resId>.<fileExt>',
    'getFile-access', RHFileAccess)
files.add_url_rule('/event/<confId>/contribution/<contribId>/material-old/<materialId>/<resId>.<fileExt>',
                   'getFile-access', RHFileAccess)

# TODO: Remove when the registration form is rewritten
files.add_url_rule('/event/<confId>/registration/attachments/<registrantId>-<resId>.<fileExt>', 'getFile-access',
                   RHFileAccess)
