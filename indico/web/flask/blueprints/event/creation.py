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
from flask import url_for
from werkzeug.utils import redirect

from MaKaC.webinterface.rh import categoryDisplay
from indico.web.flask.wrappers import IndicoBlueprint


def _redirect_simple_event(**kwargs):
    # simple_event is confusing so we always use "lecture" in the URL
    return redirect(url_for('.conferenceCreation', event_type='lecture', **kwargs))


event_creation = IndicoBlueprint('event_creation', __name__, url_prefix='/event/create')

# Event creation
event_creation.add_url_rule('/simple_event', view_func=_redirect_simple_event)
event_creation.add_url_rule('/<any(lecture,meeting,conference):event_type>', 'conferenceCreation',
                            categoryDisplay.RHConferenceCreation)
event_creation.add_url_rule('/save', 'conferenceCreation-createConference', categoryDisplay.RHConferencePerformCreation,
                            methods=('POST',))

# Event creation - category specified
event_creation.add_url_rule('!/category/<categId>/create/event/simple_event', view_func=_redirect_simple_event)
event_creation.add_url_rule('!/category/<categId>/create/event/<any(lecture,meeting,conference):event_type>',
                            'conferenceCreation', categoryDisplay.RHConferenceCreation)
