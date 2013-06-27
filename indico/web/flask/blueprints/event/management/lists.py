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


# Speakers
event_mgmt.add_url_rule('/lists/speakers', 'confModifListings-allSpeakers',
                        rh_as_view(conferenceModif.RHConfAllSpeakers))
event_mgmt.add_url_rule('/lists/speakers', 'confModifListings-allSpeakersAction',
                        rh_as_view(conferenceModif.RHConfAllSpeakersAction), methods=('POST',))
event_mgmt.add_url_rule('/lists/speakers/email/send', 'EMail-sendcontribparticipants',
                        rh_as_view(conferenceModif.RHContribParticipantsSendEmail), methods=('POST',))

# Conveners
event_mgmt.add_url_rule('/lists/conveners', 'confModifTools-allSessionsConveners',
                        rh_as_view(conferenceModif.RHConfAllSessionsConveners))
event_mgmt.add_url_rule('/lists/conveners', 'confModifTools-allSessionsConvenersAction',
                        rh_as_view(conferenceModif.RHConfAllSessionsConvenersAction), methods=('POST',))
event_mgmt.add_url_rule('/lists/conveners/email/send', 'EMail-sendconvener',
                        rh_as_view(conferenceModif.RHConvenerSendEmail), methods=('POST',))

# Pending
event_mgmt.add_url_rule('/lists/pending/', 'confModifPendingQueues',
                        rh_as_view(conferenceModif.RHConfModifPendingQueues))
event_mgmt.add_url_rule('/lists/pending/<tab>', 'confModifPendingQueues',
                        rh_as_view(conferenceModif.RHConfModifPendingQueues))
event_mgmt.add_url_rule('/lists/pending/submitters', 'confModifPendingQueues-actionSubmitters',
                        rh_as_view(conferenceModif.RHConfModifPendingQueuesActionSubm), methods=('POST',),
                        defaults={'tab': 'submitters'})
event_mgmt.add_url_rule('/lists/pending/submitters', 'confModifPendingQueues-actionConfSubmitters',
                        rh_as_view(conferenceModif.RHConfModifPendingQueuesActionConfSubm), methods=('POST',),
                        defaults={'tab': 'conf_submitters'})
event_mgmt.add_url_rule('/lists/pending/managers', 'confModifPendingQueues-actionManagers',
                        rh_as_view(conferenceModif.RHConfModifPendingQueuesActionMgr), methods=('POST',),
                        defaults={'tab': 'managers'})
event_mgmt.add_url_rule('/lists/pending/coordinators', 'confModifPendingQueues-actionCoordinators',
                        rh_as_view(conferenceModif.RHConfModifPendingQueuesActionCoord), methods=('POST',),
                        defaults={'tab': 'coordinators'})
