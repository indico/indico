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

from indico.modules.users.controllers import (RHUserDashboard, RHPersonalData, RHUserPreferences, RHUserFavorites,
                                              RHUserEmails, RHUserEmailsVerify, RHUserEmailsDelete,
                                              RHUserEmailsSetPrimary, RHUserFavoritesUsersAdd,
                                              RHUserFavoritesUserRemove, RHUserFavoritesCategoryAPI,
                                              RHUserSuggestionsRemove)
from indico.web.flask.wrappers import IndicoBlueprint

users_blueprint = _bp = IndicoBlueprint('users', __name__, template_folder='templates', url_prefix='/user')

with _bp.add_prefixed_rules('/<int:user_id>'):
    _bp.add_url_rule('/dashboard/', 'user_dashboard', RHUserDashboard)
    _bp.add_url_rule('/suggestions/categories/<category_id>', 'user_suggestions_remove', RHUserSuggestionsRemove,
                     methods=('DELETE',))
    _bp.add_url_rule('/profile/', 'user_profile', RHPersonalData, methods=('GET', 'POST'))
    _bp.add_url_rule('/preferences/', 'user_preferences', RHUserPreferences, methods=('GET', 'POST'))
    _bp.add_url_rule('/favorites/', 'user_favorites', RHUserFavorites)
    _bp.add_url_rule('/favorites/users/', 'user_favorites_users_add', RHUserFavoritesUsersAdd, methods=('POST',))
    _bp.add_url_rule('/favorites/users/<int:fav_user_id>', 'user_favorites_user_remove', RHUserFavoritesUserRemove,
                     methods=('DELETE',))
    _bp.add_url_rule('/favorites/categories/<category_id>', 'user_favorites_category_api',
                     RHUserFavoritesCategoryAPI, methods=('PUT', 'DELETE'))
    _bp.add_url_rule('/emails/', 'user_emails', RHUserEmails, methods=('GET', 'POST'))
    _bp.add_url_rule('/emails/verify/<token>', 'user_emails_verify', RHUserEmailsVerify)
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
    if endpoint.startswith('users.user_') and 'user_id' not in values:
        values['user_id'] = request.view_args.get('user_id')
