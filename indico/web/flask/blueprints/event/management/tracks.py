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

from MaKaC.webinterface.rh import conferenceModif, trackModif
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.management import event_mgmt


# Tracks
event_mgmt.add_url_rule('/program/', 'confModifProgram', rh_as_view(conferenceModif.RHConfModifProgram))
event_mgmt.add_url_rule('/program/tracks/add', 'confModifProgram-addTrack',
                        rh_as_view(conferenceModif.RHConfAddTrack), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program/tracks/add/save', 'confModifProgram-performAddTrack',
                        rh_as_view(conferenceModif.RHConfPerformAddTrack), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/delete', 'confModifProgram-deleteTracks',
                        rh_as_view(conferenceModif.RHConfDelTracks), methods=('POST',))

# View/edit track
event_mgmt.add_url_rule('/program/tracks/<trackId>/', 'trackModification', rh_as_view(trackModif.RHTrackModification))
event_mgmt.add_url_rule('/program/tracks/<trackId>/down', 'confModifProgram-moveTrackDown',
                        rh_as_view(conferenceModif.RHProgramTrackDown))
event_mgmt.add_url_rule('/program/tracks/<trackId>/up', 'confModifProgram-moveTrackUp',
                        rh_as_view(conferenceModif.RHProgramTrackUp))
event_mgmt.add_url_rule('/program/tracks/<trackId>/modify', 'trackModification-modify',
                        rh_as_view(trackModif.RHTrackDataModification), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program/tracks/<trackId>/modify/save', 'trackModification-performModify',
                        rh_as_view(trackModif.RHTrackPerformDataModification), methods=('POST',))

# Track: coordinators
event_mgmt.add_url_rule('/program/tracks/<trackId>/coordinators', 'trackModifCoordination',
                        rh_as_view(trackModif.RHTrackCoordination))

# Track: abstracts
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/', 'trackModifAbstracts',
                        rh_as_view(trackModif.RHTrackAbstractList), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/direct-access', 'trackAbstractModif-directAccess',
                        rh_as_view(trackModif.RHTrackAbstractDirectAccess), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/perform-action', 'trackAbstractModif-abstractAction',
                        rh_as_view(trackModif.RHAbstractsActions), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/abstracts.pdf', 'trackAbstractModif-abstractToPDF',
                        rh_as_view(trackModif.RHAbstractToPDF), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/', 'trackAbstractModif',
                        rh_as_view(trackModif.RHTrackAbstract), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/abstract.pdf',
                        'trackAbstractModif-abstractToPDF', rh_as_view(trackModif.RHAbstractToPDF))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/accept', 'trackAbstractModif-accept',
                        rh_as_view(trackModif.RHTrackAbstractAccept), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/propose/accept',
                        'trackAbstractModif-proposeToBeAcc',
                        rh_as_view(trackModif.RHTrackAbstractPropToAccept), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/propose/reject',
                        'trackAbstractModif-proposeToBeRej',
                        rh_as_view(trackModif.RHTrackAbstractPropToReject), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/reject', 'trackAbstractModif-reject',
                        rh_as_view(trackModif.RHTrackAbstractReject), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/dupe', 'trackAbstractModif-markAsDup',
                        rh_as_view(trackModif.RHModAbstractMarkAsDup), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/dupe/undo', 'trackAbstractModif-unMarkAsDup',
                        rh_as_view(trackModif.RHModAbstractUnMarkAsDup), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/propose-track',
                        'trackAbstractModif-proposeForOtherTracks',
                        rh_as_view(trackModif.RHTrackAbstractPropForOtherTracks), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/comments/', 'trackAbstractModif-comments',
                        rh_as_view(trackModif.RHAbstractIntComments))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/comments/add',
                        'trackAbstractModif-commentNew', rh_as_view(trackModif.RHAbstractIntCommentNew),
                        methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/comments/<intCommentId>/edit',
                        'trackAbstractModif-commentEdit', rh_as_view(trackModif.RHAbstractIntCommentEdit),
                        methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/abstracts/<abstractId>/comments/<intCommentId>/delete',
                        'trackAbstractModif-commentRem', rh_as_view(trackModif.RHAbstractIntCommentRem),
                        methods=('POST',))

# Track: contributions
event_mgmt.add_url_rule('/program/tracks/<trackId>/contributions/', 'trackModContribList',
                        rh_as_view(trackModif.RHContribList), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program/tracks/<trackId>/contributions/perform-action', 'trackModContribList-contribAction',
                        rh_as_view(trackModif.RHContribsActions), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/contributions/direct-access',
                        'trackModContribList-contribQuickAccess', rh_as_view(trackModif.RHContribQuickAccess),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program/tracks/<trackId>/contributions/contributions.pdf',
                        'trackModContribList-contribsToPDF', rh_as_view(trackModif.RHContribsToPDF), methods=('POST',))
event_mgmt.add_url_rule('/program/tracks/<trackId>/contributions/participants', 'trackModContribList-participantList',
                        rh_as_view(trackModif.RHContribsParticipantList), methods=('POST',))
