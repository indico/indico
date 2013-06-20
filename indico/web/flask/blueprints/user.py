# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico. If not, see <http://www.gnu.org/licenses/>.

from flask import Blueprint

from MaKaC.webinterface.rh import login, users, api
from indico.web.flask.util import rh_as_view


user = Blueprint('user', __name__)

# Logout
user.add_url_rule('/user/logout', 'logOut', rh_as_view(login.RHSignOut))
user.add_url_rule('/user/logout/wsignout.gif', 'logoutSSOHook', rh_as_view(login.RHLogoutSSOHook))

# Login
user.add_url_rule('/user/login', 'signIn', rh_as_view(login.RHSignIn), methods=('GET', 'POST'))
user.add_url_rule('/user/login/disabled', 'signIn-disabledAccount', rh_as_view(login.RHDisabledAccount),
                  methods=('GET', 'POST'))
user.add_url_rule('/user/login/not-activated', 'signIn-unactivatedAccount', rh_as_view(login.RHUnactivatedAccount))

# Passwords
user.add_url_rule('/user/send-password', 'signIn-sendLogin', rh_as_view(login.RHSendLogin), methods=('POST',))
user.add_url_rule('/user/account/change-password', 'identityCreation-changePassword',
                  rh_as_view(users.RHUserIdentityChangePassword), methods=('GET', 'POST'))

# Registration
user.add_url_rule('/user/register/activate', 'signIn-active', rh_as_view(login.RHActive))
user.add_url_rule('/user/register/send-activation', 'signIn-sendActivation', rh_as_view(login.RHSendActivation),
                  methods=('GET', 'POST'))
user.add_url_rule('/user/register', 'userRegistration', rh_as_view(users.RHUserCreation), methods=('GET', 'POST'))
user.add_url_rule('/user/register/exists', 'userRegistration-UserExist', rh_as_view(users.RHUserExistWithIdentity))
user.add_url_rule('/user/register/success', 'userRegistration-created', rh_as_view(users.RHUserCreated),
                  methods=('GET', 'POST'))

# Identities
user.add_url_rule('/user/account/create-identity', 'identityCreation', rh_as_view(users.RHUserIdentityCreation))
user.add_url_rule('/user/account/create-identity', 'identityCreation-create', rh_as_view(users.RHUserIdentityCreation),
                  methods=('POST',))
user.add_url_rule('/user/account/delete-identity', 'identityCreation-remove', rh_as_view(users.RHUserRemoveIdentity),
                  methods=('POST',))
user.add_url_rule('/user/account/disable', 'userRegistration-disable', rh_as_view(users.RHUserDisable),
                  methods=('GET', 'POST'))
user.add_url_rule('/user/account/activate', 'userRegistration-active', rh_as_view(users.RHUserActive),
                  methods=('GET', 'POST'))

# Dashboard, Favorites, etc.
user.add_url_rule('/user/dashboard', 'userDashboard', rh_as_view(users.RHUserDashboard))
user.add_url_rule('/user/account/', 'userDetails', rh_as_view(users.RHUserDetails))
user.add_url_rule('/user/favorites', 'userBaskets', rh_as_view(users.RHUserBaskets))
user.add_url_rule('/user/preferences', 'userPreferences', rh_as_view(users.RHUserPreferences))

# API Keys
user.add_url_rule('/user/api', 'userAPI', rh_as_view(api.RHUserAPI))
user.add_url_rule('/user/api/block', 'userAPI-block', rh_as_view(api.RHUserAPIBlock), methods=('POST',))
user.add_url_rule('/user/api/create', 'userAPI-create', rh_as_view(api.RHUserAPICreate), methods=('POST',))
user.add_url_rule('/user/api/delete', 'userAPI-delete', rh_as_view(api.RHUserAPIDelete), methods=('POST',))
