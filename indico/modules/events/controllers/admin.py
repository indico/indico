# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.modules.events.views import WPReferenceTypes
from indico.modules.events.models.references import ReferenceType
from MaKaC.webinterface.rh.admins import RHAdminBase


class RHReferenceTypes(RHAdminBase):
    """Manage reference types in server admin area"""

    def _process(self):
        types = ReferenceType.find_all()
        return WPReferenceTypes.render_template('reference_types.html', external_id_types=types)
