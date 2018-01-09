# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from indico.modules.networks.controllers import (RHCreateNetworkGroup, RHDeleteNetworkGroup, RHEditNetworkGroup,
                                                 RHManageNetworks)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('networks', __name__, template_folder='templates', virtual_template_folder='networks')

_bp.add_url_rule('/admin/networks/', 'manage', RHManageNetworks)
_bp.add_url_rule('/admin/networks/create', 'create_group', RHCreateNetworkGroup, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/networks/<int:network_group_id>/', 'edit_group', RHEditNetworkGroup, methods=('GET', 'POST'))
_bp.add_url_rule('/admin/networks/<int:network_group_id>/delete', 'delete_group', RHDeleteNetworkGroup,
                 methods=('GET', 'POST'))
