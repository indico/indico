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

from MaKaC.webinterface.rh import conferenceDisplay
from indico.web.flask.blueprints.event.display import event


# Login
event.add_url_rule('/user/login', 'confLogin', conferenceDisplay.RHConfSignIn, methods=('GET', 'POST'))
event.add_url_rule('/user/login/disabled', 'confLogin-disabledAccount', conferenceDisplay.RHConfDisabledAccount,
                   methods=('GET', 'POST'))
event.add_url_rule('/user/login/not-activated', 'confLogin-unactivatedAccount',
                   conferenceDisplay.RHConfUnactivatedAccount)
event.add_url_rule('/user/reset-password', 'confLogin-sendLogin', conferenceDisplay.RHConfSendLogin, methods=('POST',))
event.add_url_rule('/user/reset-password/<token>', 'confLogin-resetPassword', conferenceDisplay.RHConfResetPassword,
                   methods=('GET', 'POST',))

# Registration
event.add_url_rule('/user/register', 'confUser', conferenceDisplay.RHConfUserCreation, methods=('GET', 'POST'))
event.add_url_rule('/user/register/success', 'confUser-created', conferenceDisplay.RHConfUserCreated)
event.add_url_rule('/user/register/exists', 'confUser-userExists', conferenceDisplay.RHConfUserExistWithIdentity,
                   methods=('GET', 'POST'))
event.add_url_rule('/user/register/activate', 'confLogin-active', conferenceDisplay.RHConfActivate)
event.add_url_rule('/user/register/send-activation', 'confLogin-sendActivation', conferenceDisplay.RHConfSendActivation,
                   methods=('GET', 'POST'))
