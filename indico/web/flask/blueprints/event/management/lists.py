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

from MaKaC.webinterface.rh import conferenceModif
from indico.web.flask.blueprints.event.management import event_mgmt


# Speakers
event_mgmt.add_url_rule('/lists/speakers', 'confModifListings-allSpeakers', conferenceModif.RHConfAllSpeakers)
event_mgmt.add_url_rule('/lists/speakers', 'confModifListings-allSpeakersAction',
                        conferenceModif.RHConfAllSpeakersAction, methods=('POST',))
event_mgmt.add_url_rule('/lists/speakers/email/send', 'EMail-sendcontribparticipants',
                        conferenceModif.RHContribParticipantsSendEmail, methods=('POST',))

# Conveners
event_mgmt.add_url_rule('/lists/conveners', 'confModifTools-allSessionsConveners',
                        conferenceModif.RHConfAllSessionsConveners)
event_mgmt.add_url_rule('/lists/conveners', 'confModifTools-allSessionsConvenersAction',
                        conferenceModif.RHConfAllSessionsConvenersAction, methods=('POST',))
event_mgmt.add_url_rule('/lists/conveners/email/send', 'EMail-sendconvener', conferenceModif.RHConvenerSendEmail,
                        methods=('POST',))

# Pending
event_mgmt.add_url_rule('/lists/pending/', 'confModifPendingQueues', conferenceModif.RHConfModifPendingQueues)
event_mgmt.add_url_rule('/lists/pending/<tab>', 'confModifPendingQueues', conferenceModif.RHConfModifPendingQueues)
event_mgmt.add_url_rule('/lists/pending/submitters', 'confModifPendingQueues-actionSubmitters',
                        conferenceModif.RHConfModifPendingQueuesActionSubm, methods=('POST',),
                        defaults={'tab': 'submitters'})
event_mgmt.add_url_rule('/lists/pending/conf-submitters', 'confModifPendingQueues-actionConfSubmitters',
                        conferenceModif.RHConfModifPendingQueuesActionConfSubm, methods=('POST',),
                        defaults={'tab': 'conf_submitters'})
event_mgmt.add_url_rule('/lists/pending/conf-managers', 'confModifPendingQueues-actionConfManagers',
                        conferenceModif.RHConfModifPendingQueuesActionConfMgr, methods=('POST',),
                        defaults={'tab': 'conf_managers'})
event_mgmt.add_url_rule('/lists/pending/managers', 'confModifPendingQueues-actionManagers',
                        conferenceModif.RHConfModifPendingQueuesActionMgr, methods=('POST',),
                        defaults={'tab': 'managers'})
event_mgmt.add_url_rule('/lists/pending/coordinators', 'confModifPendingQueues-actionCoordinators',
                        conferenceModif.RHConfModifPendingQueuesActionCoord, methods=('POST',),
                        defaults={'tab': 'coordinators'})
