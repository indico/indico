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

from MaKaC.webinterface.rh import conferenceDisplay
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.display import event


# Login
event.add_url_rule('/<confId>/user/login', 'confLogin', rh_as_view(conferenceDisplay.RHConfSignIn),
                   methods=('GET', 'POST'))
event.add_url_rule('/<confId>/user/login/disabled', 'confLogin-disabledAccount',
                   rh_as_view(conferenceDisplay.RHConfDisabledAccount), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/user/login/not-activated', 'confLogin-unactivatedAccount',
                   rh_as_view(conferenceDisplay.RHConfUnactivatedAccount))
event.add_url_rule('/<confId>/user/send-password', 'confLogin-sendLogin', rh_as_view(conferenceDisplay.RHConfSendLogin),
                   methods=('POST',))

# Registration
event.add_url_rule('/<confId>/user/register', 'confUser', rh_as_view(conferenceDisplay.RHConfUserCreation),
                   methods=('GET', 'POST'))
event.add_url_rule('/<confId>/user/register/success', 'confUser-created',
                   rh_as_view(conferenceDisplay.RHConfUserCreated))
event.add_url_rule('/<confId>/user/register/exists', 'confUser-userExists',
                   rh_as_view(conferenceDisplay.RHConfUserExistWithIdentity), methods=('GET', 'POST'))
event.add_url_rule('/<confId>/user/register/activate', 'confLogin-active', rh_as_view(conferenceDisplay.RHConfActivate))
event.add_url_rule('/<confId>/user/register/send-activation', 'confLogin-sendActivation',
                   rh_as_view(conferenceDisplay.RHConfSendActivation), methods=('GET', 'POST'))
