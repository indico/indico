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

from indico.web.flask.util import rh_as_view
from indico.web.flask.wrappers import IndicoBlueprint

import MaKaC.webinterface.rh.conferenceModif as mod_rh_conferenceModif
import MaKaC.webinterface.rh.users as mod_rh_users
import MaKaC.webinterface.rh.xmlGateway as mod_rh_xmlGateway


legacy = IndicoBlueprint('legacy', __name__)


# Routes for confModifTools.py
legacy.add_url_rule('/confModifTools.py/dvdCreation',
                    'confModifTools-dvdCreation',
                    rh_as_view(mod_rh_conferenceModif.RHConfDVDCreation),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/confModifTools.py/dvdDone',
                    'confModifTools-dvdDone',
                    rh_as_view(mod_rh_conferenceModif.RHConfDVDDone),
                    methods=('GET', 'POST'))


# Routes for userSelection.py
legacy.add_url_rule('/userSelection.py/createExternalUsers',
                    'userSelection-createExternalUsers',
                    rh_as_view(mod_rh_users.RHCreateExternalUsers),
                    methods=('GET', 'POST'))


# Routes for xmlGateway.py
legacy.add_url_rule('/xmlGateway.py',
                    'xmlGateway',
                    rh_as_view(mod_rh_xmlGateway.RHLoginStatus),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/getCategoryInfo',
                    'xmlGateway-getCategoryInfo',
                    rh_as_view(mod_rh_xmlGateway.RHCategInfo),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/getStatsIndico',
                    'xmlGateway-getStatsIndico',
                    rh_as_view(mod_rh_xmlGateway.RHStatsIndico),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/getStatsRoomBooking',
                    'xmlGateway-getStatsRoomBooking',
                    rh_as_view(mod_rh_xmlGateway.RHStatsRoomBooking),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/loginStatus',
                    'xmlGateway-loginStatus',
                    rh_as_view(mod_rh_xmlGateway.RHLoginStatus),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/signIn',
                    'xmlGateway-signIn',
                    rh_as_view(mod_rh_xmlGateway.RHSignIn),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/signOut',
                    'xmlGateway-signOut',
                    rh_as_view(mod_rh_xmlGateway.RHSignOut),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/webcastForthcomingEvents',
                    'xmlGateway-webcastForthcomingEvents',
                    rh_as_view(mod_rh_xmlGateway.RHWebcastForthcomingEvents),
                    methods=('GET', 'POST'))

legacy.add_url_rule('/xmlGateway.py/webcastOnAir',
                    'xmlGateway-webcastOnAir',
                    rh_as_view(mod_rh_xmlGateway.RHWebcastOnAir),
                    methods=('GET', 'POST'))
