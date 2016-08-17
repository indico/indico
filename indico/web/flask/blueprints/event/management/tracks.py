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

from MaKaC.webinterface.rh import conferenceModif, trackModif
from indico.web.flask.blueprints.event.management import event_mgmt


# Tracks
event_mgmt.add_url_rule('/program-old/', 'confModifProgram', conferenceModif.RHConfModifProgram)
event_mgmt.add_url_rule('/program-old/tracks/add', 'confModifProgram-addTrack', conferenceModif.RHConfAddTrack,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program-old/tracks/add/save', 'confModifProgram-performAddTrack',
                        conferenceModif.RHConfPerformAddTrack, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/delete', 'confModifProgram-deleteTracks', conferenceModif.RHConfDelTracks,
                        methods=('POST',))

# View/edit track
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/', 'trackModification', trackModif.RHTrackModification)
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/down', 'confModifProgram-moveTrackDown',
                        conferenceModif.RHProgramTrackDown)
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/up', 'confModifProgram-moveTrackUp',
                        conferenceModif.RHProgramTrackUp)
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/modify', 'trackModification-modify',
                        trackModif.RHTrackDataModification, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/modify/save', 'trackModification-performModify',
                        trackModif.RHTrackPerformDataModification, methods=('POST',))

# Track: coordinators
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/coordinators', 'trackModifCoordination',
                        trackModif.RHTrackCoordination)

# Track: abstracts
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/', 'trackModifAbstracts',
                        trackModif.RHTrackAbstractList, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/direct-access', 'trackAbstractModif-directAccess',
                        trackModif.RHTrackAbstractDirectAccess, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/perform-action', 'trackAbstractModif-abstractAction',
                        trackModif.RHAbstractsActions, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/abstracts.pdf', 'trackAbstractModif-abstractToPDF',
                        trackModif.RHAbstractToPDF, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/', 'trackAbstractModif',
                        trackModif.RHTrackAbstract, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/abstract.pdf',
                        'trackAbstractModif-abstractToPDF', trackModif.RHAbstractToPDF)
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/accept', 'trackAbstractModif-accept',
                        trackModif.RHTrackAbstractAccept, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/propose/accept',
                        'trackAbstractModif-proposeToBeAcc', trackModif.RHTrackAbstractPropToAccept, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/propose/reject',
                        'trackAbstractModif-proposeToBeRej', trackModif.RHTrackAbstractPropToReject, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/reject', 'trackAbstractModif-reject',
                        trackModif.RHTrackAbstractReject, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/dupe', 'trackAbstractModif-markAsDup',
                        trackModif.RHModAbstractMarkAsDup, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/dupe/undo',
                        'trackAbstractModif-unMarkAsDup', trackModif.RHModAbstractUnMarkAsDup, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/propose-track',
                        'trackAbstractModif-proposeForOtherTracks', trackModif.RHTrackAbstractPropForOtherTracks,
                        methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/comments/',
                        'trackAbstractModif-comments', trackModif.RHAbstractIntComments)
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/comments/add',
                        'trackAbstractModif-commentNew', trackModif.RHAbstractIntCommentNew, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/comments/<intCommentId>/edit',
                        'trackAbstractModif-commentEdit', trackModif.RHAbstractIntCommentEdit, methods=('POST',))
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/abstracts/<abstractId>/comments/<intCommentId>/delete',
                        'trackAbstractModif-commentRem', trackModif.RHAbstractIntCommentRem, methods=('POST',))

# Track: contributions
event_mgmt.add_url_rule('/program-old/tracks/<trackId>/contributions/', 'trackModContribList',
                        trackModif.RHContribList, methods=('GET', 'POST'))
