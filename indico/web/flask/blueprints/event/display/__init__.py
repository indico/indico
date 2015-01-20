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

event = IndicoBlueprint('event', __name__, url_prefix='/event/<confId>')

import indico.web.flask.blueprints.event.display.main
import indico.web.flask.blueprints.event.display.abstracts
import indico.web.flask.blueprints.event.display.paperreviewing
import indico.web.flask.blueprints.event.display.contributions
import indico.web.flask.blueprints.event.display.schedule
import indico.web.flask.blueprints.event.display.evaluation
import indico.web.flask.blueprints.event.display.registration
import indico.web.flask.blueprints.event.display.users
import indico.web.flask.blueprints.event.display.misc
