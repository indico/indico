# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import request

from indico.modules.users.api import RHUserFavoritesAPI, fetch_authenticated_user
from indico.modules.users.controllers import (RHAcceptRegistrationRequest, RHAdmins, RHExportDashboardICS,
                                              RHPersonalData, RHProfilePictureDisplay, RHProfilePicturePage,
                                              RHProfilePicturePreview, RHRegistrationRequestList,
                                              RHRejectRegistrationRequest, RHSaveProfilePicture, RHUserBlock,
                                              RHUserDashboard, RHUserEmails, RHUserEmailsDelete, RHUserEmailsSetPrimary,
                                              RHUserEmailsVerify, RHUserFavorites, RHUserFavoritesCategoryAPI,
                                              RHUserFavoritesUserRemove, RHUserFavoritesUsersAdd, RHUserPreferences,
                                              RHUsersAdmin, RHUsersAdminCreate, RHUsersAdminMerge,
                                              RHUsersAdminMergeCheck, RHUsersAdminSettings, RHUserSearch,
                                              RHUserSearchInfo, RHUserSuggestionsRemove)
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
    # XXX: endpoint names here should start with `user_` so the `_add_user_id`
    # function below does it job properly!
    # also, when adding new code here, make sure to test acting on a different user
    # to make sure everything works correctly, ie you are not changing/showing
    # something for the wrong user (yourself)!
    _bp.add_url_rule('/dashboard/', 'user_dashboard', RHUserDashboard)
    _bp.add_url_rule('/suggestions/categories/<int:category_id>', 'user_suggestions_remove', RHUserSuggestionsRemove,
                     methods=('DELETE',))
    _bp.add_url_rule('/profile/', 'user_profile', RHPersonalData, methods=('GET', 'POST'))
    _bp.add_url_rule('/profile/picture', 'user_profile_picture_page', RHProfilePicturePage)
    _bp.add_url_rule('/profile/picture', 'save_profile_picture', RHSaveProfilePicture, methods=('POST',))
    _bp.add_url_rule('/profile/picture/preview/<any(standard,gravatar,identicon,custom):source>',
                     'profile_picture_preview', RHProfilePicturePreview)
    _bp.add_url_rule('/picture-<slug>', 'user_profile_picture_display', RHProfilePictureDisplay)
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
    _bp.add_url_rule('/blocked', 'user_block', RHUserBlock, methods=('PUT', 'DELETE'))

_bp.add_url_rule('/<int:user_id>/dashboard.ics', 'export_dashboard_ics', RHExportDashboardICS)

# User search
_bp.add_url_rule('/search/info', 'user_search_info', RHUserSearchInfo)
_bp.add_url_rule('/search/', 'user_search', RHUserSearch)

# Users API
_bp.add_url_rule('!/api/user/', 'authenticated_user', fetch_authenticated_user)

_bp.add_url_rule('/api/favorites/', 'favorites_api', RHUserFavoritesAPI)
_bp.add_url_rule('/api/favorites/<int:user_id>', 'favorites_api', RHUserFavoritesAPI, methods=('PUT', 'DELETE'))


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
