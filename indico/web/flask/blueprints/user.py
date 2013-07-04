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

from MaKaC.webinterface.rh import login, users, api
from indico.web.flask.util import rh_as_view
from indico.web.flask.wrappers import IndicoBlueprint


user = IndicoBlueprint('user', __name__, url_prefix='/user')

# Logout
user.add_url_rule('/logout', 'logOut', rh_as_view(login.RHSignOut))

# Login
user.add_url_rule('/login', 'signIn', rh_as_view(login.RHSignIn), methods=('GET', 'POST'))
user.add_url_rule('/login/sso', 'signIn-sso', rh_as_view(login.RHSignInSSO), methods=('GET', 'POST'))
user.add_url_rule('/login/sso/<authId>', 'signIn-sso', rh_as_view(login.RHSignInSSO), methods=('GET', 'POST'))
user.add_url_rule('/login/sso/<authId>/execute', 'signIn-sso-execute', build_only=True)
user.add_url_rule('/login/disabled', 'signIn-disabledAccount', rh_as_view(login.RHDisabledAccount),
                  methods=('GET', 'POST'))
user.add_url_rule('/login/not-activated', 'signIn-unactivatedAccount', rh_as_view(login.RHUnactivatedAccount))

# Passwords
user.add_url_rule('/send-password', 'signIn-sendLogin', rh_as_view(login.RHSendLogin), methods=('POST',))
with user.add_prefixed_rules('/<userId>'):
    user.add_url_rule('/account/change-password', 'identityCreation-changePassword',
                      rh_as_view(users.RHUserIdentityChangePassword), methods=('GET', 'POST'))

# Registration
user.add_url_rule('/register/activate', 'signIn-active', rh_as_view(login.RHActive))
user.add_url_rule('/register/send-activation', 'signIn-sendActivation', rh_as_view(login.RHSendActivation),
                  methods=('GET', 'POST'))
user.add_url_rule('/register', 'userRegistration', rh_as_view(users.RHUserCreation), methods=('GET', 'POST'))
user.add_url_rule('/register/exists', 'userRegistration-UserExist', rh_as_view(users.RHUserExistWithIdentity))
user.add_url_rule('/register/success', 'userRegistration-created', rh_as_view(users.RHUserCreated),
                  methods=('GET', 'POST'))


with user.add_prefixed_rules('/<userId>'):
    # Identities
    user.add_url_rule('/account/create-identity', 'identityCreation', rh_as_view(users.RHUserIdentityCreation))
    user.add_url_rule('/account/create-identity', 'identityCreation-create',
                      rh_as_view(users.RHUserIdentityCreation), methods=('POST',))
    user.add_url_rule('/account/delete-identity', 'identityCreation-remove',
                      rh_as_view(users.RHUserRemoveIdentity), methods=('POST',))
    user.add_url_rule('/account/disable', 'userRegistration-disable', rh_as_view(users.RHUserDisable),
                      methods=('GET', 'POST'))
    user.add_url_rule('/account/activate', 'userRegistration-active', rh_as_view(users.RHUserActive),
                      methods=('GET', 'POST'))

    # Dashboard, Favorites, etc.
    user.add_url_rule('/dashboard', 'userDashboard', rh_as_view(users.RHUserDashboard))
    user.add_url_rule('/account/', 'userDetails', rh_as_view(users.RHUserDetails))
    user.add_url_rule('/favorites', 'userBaskets', rh_as_view(users.RHUserBaskets))
    user.add_url_rule('/preferences', 'userPreferences', rh_as_view(users.RHUserPreferences))

    # API Keys
    user.add_url_rule('/api', 'userAPI', rh_as_view(api.RHUserAPI))
    user.add_url_rule('/api/block', 'userAPI-block', rh_as_view(api.RHUserAPIBlock), methods=('POST',))
    user.add_url_rule('/api/create', 'userAPI-create', rh_as_view(api.RHUserAPICreate), methods=('POST',))
    user.add_url_rule('/api/delete', 'userAPI-delete', rh_as_view(api.RHUserAPIDelete), methods=('POST',))
