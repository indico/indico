# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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
from indico.web.flask.wrappers import IndicoBlueprint


user = IndicoBlueprint('user', __name__, url_prefix='/user')

# Logout
user.add_url_rule('/logout', 'logOut', login.RHSignOut)

# Login
user.add_url_rule('/login', 'signIn', login.RHSignIn, methods=('GET', 'POST'))
user.add_url_rule('/login/sso', 'signIn-sso', login.RHSignInSSO, methods=('GET', 'POST'))
user.add_url_rule('/login/sso/<authId>', 'signIn-sso', login.RHSignInSSO, methods=('GET', 'POST'))
user.add_url_rule('/login/disabled', 'signIn-disabledAccount', login.RHDisabledAccount, methods=('GET', 'POST'))
user.add_url_rule('/login/not-activated', 'signIn-unactivatedAccount', login.RHUnactivatedAccount)

# Passwords
user.add_url_rule('/reset-password', 'signIn-sendLogin', login.RHSendLogin, methods=('POST',))
user.add_url_rule('/reset-password/<token>', 'signIn-resetPassword', login.RHResetPassword, methods=('GET', 'POST'))
with user.add_prefixed_rules('/<userId>'):
    user.add_url_rule('/account/change-password', 'identityCreation-changePassword', users.RHUserIdentityChangePassword,
                      methods=('GET', 'POST'))

# Registration
user.add_url_rule('/register/activate', 'signIn-active', login.RHActive)
user.add_url_rule('/register/send-activation', 'signIn-sendActivation', login.RHSendActivation, methods=('GET', 'POST'))
user.add_url_rule('/register', 'userRegistration', users.RHUserCreation, methods=('GET', 'POST'))
user.add_url_rule('/register/exists', 'userRegistration-UserExist', users.RHUserExistWithIdentity)
user.add_url_rule('/register/success', 'userRegistration-created', users.RHUserCreated, methods=('GET', 'POST'))

# Confirm email
user.add_url_rule('/account/confirm-email/<token>', 'confirm_email', users.RHConfirmEmail)

with user.add_prefixed_rules('/<userId>'):
    # Identities
    user.add_url_rule('/account/create-identity', 'identityCreation', users.RHUserIdentityCreation)
    user.add_url_rule('/account/create-identity', 'identityCreation-create', users.RHUserIdentityCreation,
                      methods=('POST',))
    user.add_url_rule('/account/delete-identity', 'identityCreation-remove', users.RHUserRemoveIdentity,
                      methods=('POST',))
    user.add_url_rule('/account/disable', 'userRegistration-disable', users.RHUserDisable, methods=('GET', 'POST'))
    user.add_url_rule('/account/activate', 'userRegistration-active', users.RHUserActive, methods=('GET', 'POST'))

    # Dashboard, Favorites, etc.
    user.add_url_rule('/dashboard', 'userDashboard', users.RHUserDashboard)
    user.add_url_rule('/account/', 'userDetails', users.RHUserDetails)
    user.add_url_rule('/favorites', 'userBaskets', users.RHUserBaskets)
    user.add_url_rule('/preferences', 'userPreferences', users.RHUserPreferences)

    # API Keys
    user.add_url_rule('/api', 'userAPI', api.RHUserAPI)
    user.add_url_rule('/api/block', 'userAPI-block', api.RHUserAPIBlock, methods=('POST',))
    user.add_url_rule('/api/create', 'userAPI-create', api.RHUserAPICreate, methods=('POST',))
    user.add_url_rule('/api/delete', 'userAPI-delete', api.RHUserAPIDelete, methods=('POST',))
