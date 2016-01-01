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

import pkg_resources
import sys

from flask import jsonify

from MaKaC.common import info
from MaKaC.webinterface.rh.base import RH


class RHSystemInfo(RH):

    def _process(self):
        try:
            indico_version = pkg_resources.get_distribution('indico').version
        except pkg_resources.DistributionNotFound:
            indico_version = 'dev'
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        stats = {'python_version': '.'.join(map(str, sys.version_info[:3])),
                 'indico_version': indico_version,
                 'language': minfo.getLang()}
        return jsonify(stats)
