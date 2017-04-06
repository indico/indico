# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from indico.modules.core.controllers import RHSettings
from indico.web.flask.util import redirect_view
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('core', __name__, template_folder='templates', virtual_template_folder='core')

_bp.add_url_rule('/admin/settings/', 'settings', RHSettings, methods=('GET', 'POST'))

# TODO: replace with an actual admin dashboard at some point
_bp.add_url_rule('/admin/', 'admin_dashboard', view_func=redirect_view('.settings'))

# Allow loadbalancers etc to easily check whether the service is alive
_bp.add_url_rule('/ping', 'ping', lambda: ('', 204))
