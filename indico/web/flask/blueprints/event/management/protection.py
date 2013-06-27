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

from MaKaC.webinterface.rh import conferenceModif
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.management import event_mgmt


# Protection
event_mgmt.add_url_rule('/access/', 'confModifAC', rh_as_view(conferenceModif.RHConfModifAC))
event_mgmt.add_url_rule('/access/visibility', 'confModifAC-setVisibility',
                        rh_as_view(conferenceModif.RHConfSetVisibility), methods=('POST',))
event_mgmt.add_url_rule('/access/session-coordinators', 'confModifAC-modifySessionCoordRights',
                        rh_as_view(conferenceModif.RHModifSessionCoordRights))
event_mgmt.add_url_rule('/access/grant/modification/conveners', 'confModifAC-grantModificationToAllConveners',
                        rh_as_view(conferenceModif.RHConfGrantModificationToAllConveners), methods=('POST',))
event_mgmt.add_url_rule('/access/grant/submission/speakers', 'confModifAC-grantSubmissionToAllSpeakers',
                        rh_as_view(conferenceModif.RHConfGrantSubmissionToAllSpeakers), methods=('POST',))
event_mgmt.add_url_rule('/access/revoke/submission', 'confModifAC-removeAllSubmissionRights',
                        rh_as_view(conferenceModif.RHConfRemoveAllSubmissionRights), methods=('POST',))
