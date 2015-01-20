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


# Material package
event.add_url_rule('/material/download', 'conferenceDisplay-matPkg', conferenceDisplay.RHFullMaterialPackage)
event.add_url_rule('/material/download', 'conferenceDisplay-performMatPkg',
                   conferenceDisplay.RHFullMaterialPackagePerform, methods=('POST',))

# My conference
event.add_url_rule('/my-conference/', 'myconference', conferenceDisplay.RHMyStuff)
event.add_url_rule('/my-conference/contributions', 'myconference-myContributions',
                   conferenceDisplay.RHConfMyStuffMyContributions)
event.add_url_rule('/my-conference/sessions', 'myconference-mySessions', conferenceDisplay.RHConfMyStuffMySessions)
event.add_url_rule('/my-conference/tracks', 'myconference-myTracks', conferenceDisplay.RHConfMyStuffMyTracks)

# Custom pages
event.add_url_rule('/page/<pageId>', 'internalPage', conferenceDisplay.RHInternalPageDisplay)

# Other views
event.add_url_rule('/other-view', 'conferenceOtherViews', conferenceDisplay.RHConferenceOtherViews)

# EMail form
event.add_url_rule('/email', 'EMail', conferenceDisplay.RHConferenceEmail, methods=('GET', 'POST'))
event.add_url_rule('/email/send', 'EMail-send', conferenceDisplay.RHConferenceSendEmail, methods=('POST',))

# Participation invitation
event.add_url_rule('/invitation/participant/<participantId>', 'confModifParticipants-invitation',
                   conferenceDisplay.RHConfParticipantsInvitation, methods=('GET', 'POST'))
event.add_url_rule('/invitation/participant/<participantId>/refuse', 'confModifParticipants-refusal',
                   conferenceDisplay.RHConfParticipantsRefusal, methods=('GET', 'POST'))
