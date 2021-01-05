# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
