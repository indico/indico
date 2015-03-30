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

from __future__ import unicode_literals

from flask import request

from indico.modules.oauth.controllers import RHOAuthUserProfile
from indico.web.flask.wrappers import IndicoBlueprint

oauth_blueprint = _bp = IndicoBlueprint('oauth', __name__, template_folder='templates')

# User profile
with _bp.add_prefixed_rules('/user/<int:user_id>', '/user'):
    _bp.add_url_rule('/oauth/', 'user_profile', RHOAuthUserProfile)


@_bp.url_defaults
def _add_user_id(endpoint, values):
    if endpoint == 'oauth.user_profile':
        # Inject user id if it's present in the url
        values['user_id'] = request.view_args.get('user_id')
