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

from flask import request

from indico.modules.users.api import fetch_authenticated_user
from indico.modules.users.controllers import (RHAcceptRegistrationRequest, RHAdmins, RHPersonalData,
                                              RHRegistrationRequestList, RHRejectRegistrationRequest, RHUserDashboard,
                                              RHUserEmails, RHUserEmailsDelete, RHUserEmailsSetPrimary,
                                              RHUserEmailsVerify, RHUserFavorites, RHUserFavoritesCategoryAPI,
                                              RHUserFavoritesUserRemove, RHUserFavoritesUsersAdd, RHUserPreferences,
                                              RHUsersAdmin, RHUsersAdminCreate, RHUsersAdminMerge,
                                              RHUsersAdminMergeCheck, RHUsersAdminSettings, RHUserSuggestionsRemove)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('users', __name__, template_folder='templates', virtual_template_folder='users',
                      url_prefix='/user')

# Admins
_bp.add_url_rule('!/admin/admins', 'admins', RHAdmins, methods=('GET', 'POST'))

# User management
_bp.add_url_rule('!/admin/users/', 'users_admin', RHUsersAdmin, methods=('GET', 'POST'))
_bp.add_url_rule('!/admin/users/settings', 'users_admin_settings', RHUsersAdminSettings, methods=('GET', 'POST'))
_bp.add_url_rule('!/admin/users/create/', 'users_create', RHUsersAdminCreate, methods=('GET', 'POST'))
_bp.add_url_rule('!/admin/users/merge/', 'users_merge', RHUsersAdminMerge, methods=('GET', 'POST'))
_bp.add_url_rule('!/admin/users/merge/check/', 'users_merge_check', RHUsersAdminMergeCheck)
_bp.add_url_rule('!/admin/users/registration-requests/', 'registration_request_list', RHRegistrationRequestList)
_bp.add_url_rule('!/admin/users/registration-requests/<int:request_id>/accept', 'accept_registration_request',
                 RHAcceptRegistrationRequest, methods=('POST',))
_bp.add_url_rule('!/admin/users/registration-requests/<int:request_id>/reject', 'reject_registration_request',
                 RHRejectRegistrationRequest, methods=('POST',))


# User profile
with _bp.add_prefixed_rules('/<int:user_id>'):
    _bp.add_url_rule('/dashboard/', 'user_dashboard', RHUserDashboard)
    _bp.add_url_rule('/suggestions/categories/<int:category_id>', 'user_suggestions_remove', RHUserSuggestionsRemove,
                     methods=('DELETE',))
    _bp.add_url_rule('/profile/', 'user_profile', RHPersonalData, methods=('GET', 'POST'))
    _bp.add_url_rule('/preferences/', 'user_preferences', RHUserPreferences, methods=('GET', 'POST'))
    _bp.add_url_rule('/favorites/', 'user_favorites', RHUserFavorites)
    _bp.add_url_rule('/favorites/users/', 'user_favorites_users_add', RHUserFavoritesUsersAdd, methods=('POST',))
    _bp.add_url_rule('/favorites/users/<int:fav_user_id>', 'user_favorites_user_remove', RHUserFavoritesUserRemove,
                     methods=('DELETE',))
    _bp.add_url_rule('/favorites/categories/<int:category_id>', 'user_favorites_category_api',
                     RHUserFavoritesCategoryAPI, methods=('PUT', 'DELETE'))
    _bp.add_url_rule('/emails/', 'user_emails', RHUserEmails, methods=('GET', 'POST'))
    _bp.add_url_rule('/emails/verify/<token>', 'user_emails_verify', RHUserEmailsVerify)
    _bp.add_url_rule('/emails/<email>', 'user_emails_delete', RHUserEmailsDelete, methods=('DELETE',))
    _bp.add_url_rule('/emails/make-primary', 'user_emails_set_primary', RHUserEmailsSetPrimary, methods=('POST',))


# Users API
_bp.add_url_rule('!/api/user/', 'authenticated_user', fetch_authenticated_user)


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
