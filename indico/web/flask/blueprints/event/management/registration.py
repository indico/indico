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

# Setup - manage form sections
event_mgmt.add_url_rule('/registration/setup/form/section/perform-action', 'confModifRegistrationForm-actionSection',
                        registrationFormModif.RHRegistrationFormActionSection, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/<section>/toggle', 'confModifRegistrationForm-enableSection',
                        registrationFormModif.RHRegistrationFormModifEnableSection)

# Setup - special form section: reason for participation
event_mgmt.add_url_rule('/registration/setup/form/section/reasonParticipation/',
                        'confModifRegistrationForm-modifReasonParticipation',
                        registrationFormModif.RHRegistrationFormModifReasonParticipation)
event_mgmt.add_url_rule('/registration/setup/form/section/reasonParticipation/modify',
                        'confModifRegistrationForm-modifReasonParticipationData',
                        registrationFormModif.RHRegistrationFormModifReasonParticipationDataModif,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/reasonParticipation/modify/save',
                        'confModifRegistrationForm-performModifReasonParticipationData',
                        registrationFormModif.RHRegistrationFormModifReasonParticipationPerformDataModif,
                        methods=('POST',))

# Setup - special form section: sessions
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/', 'confModifRegistrationForm-modifSessions',
                        registrationFormModif.RHRegistrationFormModifSessions)
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/modify',
                        'confModifRegistrationForm-modifSessionsData',
                        registrationFormModif.RHRegistrationFormModifSessionsDataModif, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/modify/save',
                        'confModifRegistrationForm-performModifSessionsData',
                        registrationFormModif.RHRegistrationFormModifSessionsPerformDataModif, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/session/remove',
                        'confModifRegistrationForm-removeSession',
                        registrationFormModif.RHRegistrationFormModifSessionsRemove, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/session/add', 'confModifRegistrationForm-addSession',
                        registrationFormModif.RHRegistrationFormModifSessionsAdd, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/session/add/save',
                        'confModifRegistrationForm-performAddSession',
                        registrationFormModif.RHRegistrationFormModifSessionsPerformAdd, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/session/<sessionId>/',
                        'confModifRegistrationForm-modifySessionItem',
                        registrationFormModif.RHRegistrationFormSessionItemModify)
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/session/<sessionId>/',
                        'confModifRegistrationForm-performModifySessionItem',
                        registrationFormModif.RHRegistrationFormSessionItemPerformModify, methods=('POST',))

# Setup - special form section: accommodation
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/',
                        'confModifRegistrationForm-modifAccommodation',
                        registrationFormModif.RHRegistrationFormModifAccommodation)
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/modify',
                        'confModifRegistrationForm-modifAccommodationData',
                        registrationFormModif.RHRegistrationFormModifAccommodationDataModif, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/modify/save',
                        'confModifRegistrationForm-performModifAccommodationData',
                        registrationFormModif.RHRegistrationFormModifAccommodationPerformDataModif, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/type/add',
                        'confModifRegistrationForm-addAccommodationType',
                        registrationFormModif.RHRegistrationFormModifAccommodationTypeAdd, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/type/add/save',
                        'confModifRegistrationForm-performAddAccommodationType',
                        registrationFormModif.RHRegistrationFormModifAccommodationTypePerformAdd, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/type/<accoTypeId>/',
                        'confModifRegistrationForm-modifyAccommodationType',
                        registrationFormModif.RHRegistrationFormAccommodationTypeModify)
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/type/<accoTypeId>/',
                        'confModifRegistrationForm-performModifyAccommodationType',
                        registrationFormModif.RHRegistrationFormAccommodationTypePerformModify, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/type/remove',
                        'confModifRegistrationForm-removeAccommodationType',
                        registrationFormModif.RHRegistrationFormModifAccommodationTypeRemove, methods=('POST',))

# Setup - special form section: social events
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/', 'confModifRegistrationForm-modifSocialEvent',
                        registrationFormModif.RHRegistrationFormModifSocialEvent)
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/modify',
                        'confModifRegistrationForm-modifSocialEventData',
                        registrationFormModif.RHRegistrationFormModifSocialEventDataModif, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/modify/save',
                        'confModifRegistrationForm-performModifSocialEventData',
                        registrationFormModif.RHRegistrationFormModifSocialEventPerformDataModif, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/event/add',
                        'confModifRegistrationForm-addSocialEvent',
                        registrationFormModif.RHRegistrationFormModifSocialEventAdd, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/event/add/save',
                        'confModifRegistrationForm-performAddSocialEvent',
                        registrationFormModif.RHRegistrationFormModifSocialEventPerformAdd, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/event/<socialEventId>/',
                        'confModifRegistrationForm-modifySocialEventItem',
                        registrationFormModif.RHRegistrationFormSocialEventItemModify)
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/event/<socialEventId>/',
                        'confModifRegistrationForm-performModifySocialEventItem',
                        registrationFormModif.RHRegistrationFormSocialEventItemPerformModify, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/event/remove',
                        'confModifRegistrationForm-removeSocialEvent',
                        registrationFormModif.RHRegistrationFormModifSocialEventRemove, methods=('POST',))

# Setup - special form section: further information
event_mgmt.add_url_rule('/registration/setup/form/section/furtherInformation/',
                        'confModifRegistrationForm-modifFurtherInformation',
                        registrationFormModif.RHRegistrationFormModifFurtherInformation)
event_mgmt.add_url_rule('/registration/setup/form/section/furtherInformation/modify',
                        'confModifRegistrationForm-modifFurtherInformationData',
                        registrationFormModif.RHRegistrationFormModifFurtherInformationDataModif,
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/furtherInformation/modify/save',
                        'confModifRegistrationForm-performModifFurtherInformationData',
                        registrationFormModif.RHRegistrationFormModifFurtherInformationPerformDataModif,
                        methods=('POST',))

# Setup - general form sections
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/',
                        'confModifRegistrationForm-modifGeneralSection',
                        registrationFormModif.RHRegistrationFormModifGeneralSection)
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/modify',
                        'confModifRegistrationForm-modifGeneralSectionData',
                        registrationFormModif.RHRegistrationFormModifGeneralSectionDataModif, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/modify/save',
                        'confModifRegistrationForm-performModifGeneralSectionData',
                        registrationFormModif.RHRegistrationFormModifGeneralSectionPerformDataModif, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/add',
                        'confModifRegistrationForm-addGeneralField',
                        registrationFormModif.RHRegistrationFormModifGeneralSectionFieldAdd, methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/add/save',
                        'confModifRegistrationForm-performAddGeneralField',
                        registrationFormModif.RHRegistrationFormModifGeneralSectionFieldPerformAdd, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/<sectionFieldId>/',
                        'confModifRegistrationForm-modifGeneralField',
                        registrationFormModif.RHRegistrationFormModifGeneralSectionFieldModif)
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/<sectionFieldId>/',
                        'confModifRegistrationForm-performModifGeneralField',
                        registrationFormModif.RHRegistrationFormModifGeneralSectionFieldPerformModif, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/perform-action',
                        'confModifRegistrationForm-removeGeneralField',
                        registrationFormModif.RHRegistrationFormModifGeneralSectionFieldProcess, methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/<personalfield>/toggle-personal',
                        'confModifRegistrationForm-enablePersonalField',
                        registrationFormModif.RHRegistrationFormModifEnablePersonalField, methods=('GET', 'POST'))

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
