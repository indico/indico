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

from flask import current_app, g

from indico.modules.events.papers.controllers import management
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('papers', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/papers')


# Display pages
# TODO...

# Management
_bp.add_url_rule('/manage/papers/', 'management', management.RHPapersDashboard)
_bp.add_url_rule('/manage/papers/teams/', 'manage_teams', management.RHManagePaperTeams,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/papers/teams/competences', 'manage_competences', management.RHManageCompetences,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/papers/enable/<any(content,layout):reviewing_type>', 'switch',
                 management.RHSwitchReviewingType, methods=('PUT', 'DELETE'))

# CFP scheduling
_bp.add_url_rule('/manage/papers/schedule', 'schedule_cfp', management.RHScheduleCFP,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/papers/open', 'open_cfp', management.RHOpenCFP, methods=('POST',))
_bp.add_url_rule('/manage/papers/close', 'close_cfp', management.RHCloseCFP, methods=('POST',))

# URLs available in both management and display areas
# Note: When adding a new one here make sure to specify `defaults=defaults`
#       for each rule. Otherwise you may not get the correct one.
for prefix, is_management in (('/manage/papers', True), ('/papers', False)):
    defaults = {'management': is_management}
    # TODO...


@_bp.url_defaults
def _add_management_flag(endpoint, values):
    if ('management' not in values and
            endpoint.split('.')[0] == _bp.name and
            current_app.url_map.is_endpoint_expecting(endpoint, 'management')):
        values['management'] = g.rh.management


# Legacy URLs
_compat_bp = IndicoBlueprint('compat_papers', __name__, url_prefix='/event/<int:confId>')
# TODO...
