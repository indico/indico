# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from MaKaC.webinterface.rh import categoryDisplay
from indico.web.flask.wrappers import IndicoBlueprint


event_creation = IndicoBlueprint('event_creation', __name__, url_prefix='/event/create-old')

# Event creation
event_creation.add_url_rule('/<any(lecture,meeting,conference):event_type>', 'conferenceCreation',
                            categoryDisplay.RHConferenceCreation)
event_creation.add_url_rule('/<any(lecture,meeting,conference):event_type>/save', 'conferenceCreation-createConference',
                            categoryDisplay.RHConferencePerformCreation, methods=('POST',))

# Event creation - category specified
event_creation.add_url_rule(
    '!/category/<int:category_id>/create-old/event/<any(lecture,meeting,conference):event_type>',
    'conferenceCreation', categoryDisplay.RHConferenceCreation)
event_creation.add_url_rule(
    '!/category/<int:category_id>/create-old/event/<any(lecture,meeting,conference):event_type>/save',
    'conferenceCreation-createConference', categoryDisplay.RHConferencePerformCreation, methods=('POST',))
