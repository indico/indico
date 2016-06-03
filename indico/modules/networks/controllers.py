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


from indico.modules.networks.forms import IPNetworkGroupForm
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.modules.networks.views import WPNetworksAdmin
from indico.web.util import jsonify_form
from MaKaC.webinterface.rh.admins import RHAdminBase


class RHManageNetworks(RHAdminBase):
    """Management list for IPNetworks"""

    def _process(self):
        network_groups = IPNetworkGroup.find().order_by(IPNetworkGroup.name).all()
        return WPNetworksAdmin.render_template('networks.html', network_groups=network_groups)


class RHCreateIPNetworkGroup(RHAdminBase):
    """Dialog to create an IPNetworkGroup"""

    def _process(self):
        form = IPNetworkGroupForm()
        if form.validate_on_submit():
            pass
        return jsonify_form(form)
