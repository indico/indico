# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request

from indico.modules.admin.views import WPAdmin
from indico.modules.users import User
from indico.util.i18n import _
from indico.web.breadcrumbs import render_breadcrumbs
from indico.web.views import WPDecorated, WPJinjaMixin


class WPUser(WPJinjaMixin, WPDecorated):
    """Base WP for user profile pages.

    Whenever you use this, you MUST include `user` in the params passed to
    `render_template`. Any RH using this should inherit from `RHUserBase`
    which already handles user/admin access. In this case, simply add
    ``user=self.user`` to your `render_template` call.
    """

    template_prefix = 'users/'
    ALLOW_JSON = False

    def __init__(self, rh, active_menu_item, **kwargs):
        kwargs['active_menu_item'] = active_menu_item
        WPDecorated.__init__(self, rh, **kwargs)

    def _get_user_page_title(self):
        if 'user_id' in request.view_args:
            user = User.get(request.view_args['user_id'])
            return _('Profile of {name}').format(name=user.full_name)
        else:
            return _('My Profile')

    @property
    def _extra_title_parts(self):
        return [self._get_user_page_title()]

    def _get_breadcrumbs(self):
        return render_breadcrumbs(self._get_user_page_title())

    def _get_body(self, params):
        return self._get_page_content(params)


class WPUserDashboard(WPUser):
    bundles = ('module_users.dashboard.js',)


class WPUserProfilePic(WPUser):
    bundles = ('module_users.profile_picture.js', 'module_users.profile_picture.css')


class WPUserPersonalData(WPUser):
    bundles = ('module_users.personal_data.js', 'module_users.personal_data.css')


class WPUserFavorites(WPUser):
    bundles = ('module_users.favorites.js', 'module_users.favorites.css')


class WPUserDataExport(WPUser):
    bundles = ('module_users.data_export.js', 'module_users.data_export.css')


class WPUsersAdmin(WPAdmin):
    template_prefix = 'users/'
    bundles = ('module_users.js',)
