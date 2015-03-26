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

from indico.modules.users.controllers import (RHUserDashboard, RHUserAccount, RHUserPreferences, RHUserFavorites,
                                              RHUserEmails, RHUserEmailsDelete, RHUserEmailsSetPrimary)
from indico.web.flask.wrappers import IndicoBlueprint

# TODO: remove -new later
users_blueprint = _bp = IndicoBlueprint('users', __name__, template_folder='templates', url_prefix='/user-new')

with _bp.add_prefixed_rules('/<int:user_id>'):
    _bp.add_url_rule('/dashboard/', 'user_dashboard', RHUserDashboard)
    _bp.add_url_rule('/account/', 'user_account', RHUserAccount)
    _bp.add_url_rule('/preferences/', 'user_preferences', RHUserPreferences)
    _bp.add_url_rule('/favorites/', 'user_favorites', RHUserFavorites)
    _bp.add_url_rule('/emails/', 'user_emails', RHUserEmails, methods=('GET', 'POST'))
    _bp.add_url_rule('/emails/<email>', 'user_emails_delete', RHUserEmailsDelete, methods=('DELETE',))
    _bp.add_url_rule('/emails/make-primary', 'users_emails_set_primary', RHUserEmailsSetPrimary, methods=('POST',))


@_bp.url_defaults
def _add_user_id(endpoint, values):
    """Add user id to user-specific urls if one was set for the current page.

    This ensures that the URLs we have both with an without user id always
    preserve the user id if there is one, but regular users don't end up
    with the user id in the URL all the time.

    Note that this needs to be replicated in other blueprints when they add
    stuff to the user pages using the `user_sidemenu` signal.
    """
    if endpoint.startswith('users.user_'):
        values['user_id'] = request.view_args.get('user_id')
