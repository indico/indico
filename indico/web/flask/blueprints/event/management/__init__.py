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

from indico.web.flask.wrappers import IndicoBlueprint

event_mgmt = IndicoBlueprint('event_mgmt', __name__, url_prefix='/event/<confId>/manage')

import indico.web.flask.blueprints.event.management.main
import indico.web.flask.blueprints.event.management.general
import indico.web.flask.blueprints.event.management.tools
import indico.web.flask.blueprints.event.management.layout
import indico.web.flask.blueprints.event.management.protection
import indico.web.flask.blueprints.event.management.lists
import indico.web.flask.blueprints.event.management.evaluation
import indico.web.flask.blueprints.event.management.rooms
import indico.web.flask.blueprints.event.management.registration
import indico.web.flask.blueprints.event.management.payment
import indico.web.flask.blueprints.event.management.abstracts
import indico.web.flask.blueprints.event.management.tracks
import indico.web.flask.blueprints.event.management.schedule
import indico.web.flask.blueprints.event.management.participants
import indico.web.flask.blueprints.event.management.contributions
import indico.web.flask.blueprints.event.management.sessions
import indico.web.flask.blueprints.event.management.paperreviewing
import indico.web.flask.blueprints.event.management.misc
import indico.web.flask.blueprints.event.management.eticket
