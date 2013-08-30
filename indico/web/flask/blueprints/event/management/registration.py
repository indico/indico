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

from MaKaC.webinterface.rh import registrationFormModif, registrantsModif
from indico.web.flask.blueprints.event.management import event_mgmt


# Setup
event_mgmt.add_url_rule('/registration/setup/', 'confModifRegistrationForm',
                        registrationFormModif.RHRegistrationFormModif)
event_mgmt.add_url_rule('/registration/setup/change-status', 'confModifRegistrationForm-changeStatus',
                        registrationFormModif.RHRegistrationFormModifChangeStatus, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/modify', 'confModifRegistrationForm-dataModif',
                        registrationFormModif.RHRegistrationFormModifDataModification, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/modify/save', 'confModifRegistrationForm-performDataModif',
                        registrationFormModif.RHRegistrationFormModifPerformDataModification, methods=('POST',))

# Setup - statuses
event_mgmt.add_url_rule('/registration/setup/statuses/perform-action', 'confModifRegistrationForm-actionStatuses',
                        registrationFormModif.RHRegistrationFormActionStatuses, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/statuses/<statusId>/modify', 'confModifRegistrationForm-modifStatus',
                        registrationFormModif.RHRegistrationFormStatusModif)
event_mgmt.add_url_rule('/registration/setup/statuses/<statusId>/modify',
                        'confModifRegistrationForm-performModifStatus',
                        registrationFormModif.RHRegistrationFormModifStatusPerformModif, methods=('POST',))

# Preview
event_mgmt.add_url_rule('/registration/preview', 'confModifRegistrationPreview',
                        registrationFormModif.RHRegistrationPreview)

# Registrants
event_mgmt.add_url_rule('/registration/users/', 'confModifRegistrants', registrantsModif.RHRegistrantListModif,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/perform-action', 'confModifRegistrants-action',
                        registrantsModif.RHRegistrantListModifAction, methods=('POST',))
event_mgmt.add_url_rule('/registration/users/email/send', 'EMail-sendreg', registrantsModif.RHRegistrantSendEmail,
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/users/new', 'confModifRegistrants-newRegistrant',
                        registrantsModif.RHRegistrantNewForm, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/remove', 'confModifRegistrants-remove',
                        registrantsModif.RHRegistrantListRemove, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/', 'confModifRegistrants-modification',
                        registrantsModif.RHRegistrantModification)
event_mgmt.add_url_rule('/registration/users/<registrantId>/eticket',
                        'confModifRegistrants-modification-eticket',
                        registrantsModif.RHRegistrantModificationEticket)
event_mgmt.add_url_rule('/registration/users/<registrantId>/eticket/checkin',
                        'confModifRegistrants-modification-eticket-checkin',
                        registrantsModif.RHRegistrantModificationEticketCheckIn,
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/users/<registrantId>/attachments/<resId>.<fileExt>',
                        'confModifRegistrants-getAttachedFile', registrantsModif.RHGetAttachedFile)
# Misc sections and personal data
event_mgmt.add_url_rule('/registration/users/<registrantId>/misc/<miscInfoId>', 'confModifRegistrants-modifyMiscInfo',
                        registrantsModif.RHRegistrantMiscInfoModify, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/misc/<miscInfoId>/save',
                        'confModifRegistrants-performModifyMiscInfo',
                        registrantsModif.RHRegistrantMiscInfoPerformModify, methods=('POST',))
# Accommodation
event_mgmt.add_url_rule('/registration/users/<registrantId>/accommodation', 'confModifRegistrants-modifyAccommodation',
                        registrantsModif.RHRegistrantAccommodationModify, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/accommodation/save',
                        'confModifRegistrants-performModifyAccommodation',
                        registrantsModif.RHRegistrantAccommodationPerformModify, methods=('POST',))
# Reason for participation
event_mgmt.add_url_rule('/registration/users/<registrantId>/reasonParticipation',
                        'confModifRegistrants-modifyReasonParticipation',
                        registrantsModif.RHRegistrantReasonParticipationModify, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/reasonParticipation/save',
                        'confModifRegistrants-performModifyReasonParticipation',
                        registrantsModif.RHRegistrantReasonParticipationPerformModify, methods=('POST',))
# Sessions
event_mgmt.add_url_rule('/registration/users/<registrantId>/sessions', 'confModifRegistrants-modifySessions',
                        registrantsModif.RHRegistrantSessionModify, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/sessions/save',
                        'confModifRegistrants-performModifySessions', registrantsModif.RHRegistrantSessionPerformModify,
                        methods=('POST',))
# Social events
event_mgmt.add_url_rule('/registration/users/<registrantId>/socialEvents', 'confModifRegistrants-modifySocialEvents',
                        registrantsModif.RHRegistrantSocialEventsModify, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/socialEvents/save',
                        'confModifRegistrants-performModifySocialEvents',
                        registrantsModif.RHRegistrantSocialEventsPerformModify, methods=('POST',))
# Statuses
event_mgmt.add_url_rule('/registration/users/<registrantId>/statuses', 'confModifRegistrants-modifyStatuses',
                        registrantsModif.RHRegistrantStatusesModify, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/statuses/save',
                        'confModifRegistrants-performModifyStatuses',
                        registrantsModif.RHRegistrantStatusesPerformModify, methods=('POST',))
# Payment
event_mgmt.add_url_rule('/registration/users/<registrantId>/payment', 'confModifRegistrants-modifyTransaction',
                        registrantsModif.RHRegistrantTransactionModify, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/payment/save',
                        'confModifRegistrants-peformModifyTransaction',
                        registrantsModif.RHRegistrantTransactionPerformModify, methods=('POST',))
