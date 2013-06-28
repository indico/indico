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
from indico.web.flask.util import rh_as_view
from indico.web.flask.blueprints.event.management import event_mgmt


# Setup
event_mgmt.add_url_rule('/registration/setup/', 'confModifRegistrationForm',
                        rh_as_view(registrationFormModif.RHRegistrationFormModif))
event_mgmt.add_url_rule('/registration/setup/change-status', 'confModifRegistrationForm-changeStatus',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifChangeStatus), methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/modify', 'confModifRegistrationForm-dataModif',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifDataModification),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/modify/save', 'confModifRegistrationForm-performDataModif',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifPerformDataModification),
                        methods=('POST',))

# Setup - statuses
event_mgmt.add_url_rule('/registration/setup/statuses/perform-action', 'confModifRegistrationForm-actionStatuses',
                        rh_as_view(registrationFormModif.RHRegistrationFormActionStatuses), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/statuses/<statusId>/modify', 'confModifRegistrationForm-modifStatus',
                        rh_as_view(registrationFormModif.RHRegistrationFormStatusModif))
event_mgmt.add_url_rule('/registration/setup/statuses/<statusId>/modify',
                        'confModifRegistrationForm-performModifStatus',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifStatusPerformModif),
                        methods=('POST',))

# Setup - manage form sections
event_mgmt.add_url_rule('/registration/setup/form/section/perform-action', 'confModifRegistrationForm-actionSection',
                        rh_as_view(registrationFormModif.RHRegistrationFormActionSection), methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/<section>/toggle', 'confModifRegistrationForm-enableSection',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifEnableSection))

# Setup - special form section: reason for participation
event_mgmt.add_url_rule('/registration/setup/form/section/reasonParticipation/',
                        'confModifRegistrationForm-modifReasonParticipation',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifReasonParticipation))
event_mgmt.add_url_rule('/registration/setup/form/section/reasonParticipation/modify',
                        'confModifRegistrationForm-modifReasonParticipationData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifReasonParticipationDataModif),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/reasonParticipation/modify/save',
                        'confModifRegistrationForm-performModifReasonParticipationData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifReasonParticipationPerformDataModif),
                        methods=('POST',))

# Setup - special form section: sessions
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/', 'confModifRegistrationForm-modifSessions',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSessions))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/modify',
                        'confModifRegistrationForm-modifSessionsData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSessionsDataModif),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/modify/save',
                        'confModifRegistrationForm-performModifSessionsData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSessionsPerformDataModif),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/session/remove',
                        'confModifRegistrationForm-removeSession',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSessionsRemove),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/session/add', 'confModifRegistrationForm-addSession',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSessionsAdd), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/session/add/save',
                        'confModifRegistrationForm-performAddSession',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSessionsPerformAdd), methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/session/<sessionId>/',
                        'confModifRegistrationForm-modifySessionItem',
                        rh_as_view(registrationFormModif.RHRegistrationFormSessionItemModify))
event_mgmt.add_url_rule('/registration/setup/form/section/sessions/session/<sessionId>/',
                        'confModifRegistrationForm-performModifySessionItem',
                        rh_as_view(registrationFormModif.RHRegistrationFormSessionItemPerformModify),
                        methods=('POST',))

# Setup - special form section: accommodation
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/',
                        'confModifRegistrationForm-modifAccommodation',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifAccommodation))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/modify',
                        'confModifRegistrationForm-modifAccommodationData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifAccommodationDataModif),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/modify/save',
                        'confModifRegistrationForm-performModifAccommodationData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifAccommodationPerformDataModif),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/type/add',
                        'confModifRegistrationForm-addAccommodationType',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifAccommodationTypeAdd),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/type/add/save',
                        'confModifRegistrationForm-performAddAccommodationType',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifAccommodationTypePerformAdd),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/type/<accoTypeId>/',
                        'confModifRegistrationForm-modifyAccommodationType',
                        rh_as_view(registrationFormModif.RHRegistrationFormAccommodationTypeModify))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/type/<accoTypeId>/',
                        'confModifRegistrationForm-performModifyAccommodationType',
                        rh_as_view(registrationFormModif.RHRegistrationFormAccommodationTypePerformModify),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/accommodation/type/remove',
                        'confModifRegistrationForm-removeAccommodationType',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifAccommodationTypeRemove),
                        methods=('POST',))

# Setup - special form section: social events
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/', 'confModifRegistrationForm-modifSocialEvent',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSocialEvent))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/modify',
                        'confModifRegistrationForm-modifSocialEventData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSocialEventDataModif),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/modify/save',
                        'confModifRegistrationForm-performModifSocialEventData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSocialEventPerformDataModif),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/event/add',
                        'confModifRegistrationForm-addSocialEvent',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSocialEventAdd),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/event/add/save',
                        'confModifRegistrationForm-performAddSocialEvent',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSocialEventPerformAdd),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/event/<socialEventId>/',
                        'confModifRegistrationForm-modifySocialEventItem',
                        rh_as_view(registrationFormModif.RHRegistrationFormSocialEventItemModify))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/event/<socialEventId>/',
                        'confModifRegistrationForm-performModifySocialEventItem',
                        rh_as_view(registrationFormModif.RHRegistrationFormSocialEventItemPerformModify),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/socialEvents/event/remove',
                        'confModifRegistrationForm-removeSocialEvent',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifSocialEventRemove), methods=('POST',))

# Setup - special form section: further information
event_mgmt.add_url_rule('/registration/setup/form/section/furtherInformation/',
                        'confModifRegistrationForm-modifFurtherInformation',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifFurtherInformation))
event_mgmt.add_url_rule('/registration/setup/form/section/furtherInformation/modify',
                        'confModifRegistrationForm-modifFurtherInformationData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifFurtherInformationDataModif),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/furtherInformation/modify/save',
                        'confModifRegistrationForm-performModifFurtherInformationData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifFurtherInformationPerformDataModif),
                        methods=('POST',))

# Setup - general form sections
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/',
                        'confModifRegistrationForm-modifGeneralSection',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifGeneralSection))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/modify',
                        'confModifRegistrationForm-modifGeneralSectionData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifGeneralSectionDataModif),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/modify/save',
                        'confModifRegistrationForm-performModifGeneralSectionData',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifGeneralSectionPerformDataModif),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/add',
                        'confModifRegistrationForm-addGeneralField',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifGeneralSectionFieldAdd),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/add/save',
                        'confModifRegistrationForm-performAddGeneralField',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifGeneralSectionFieldPerformAdd),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/<sectionFieldId>/',
                        'confModifRegistrationForm-modifGeneralField',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifGeneralSectionFieldModif))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/<sectionFieldId>/',
                        'confModifRegistrationForm-performModifGeneralField',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifGeneralSectionFieldPerformModif),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/perform-action',
                        'confModifRegistrationForm-removeGeneralField',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifGeneralSectionFieldProcess),
                        methods=('POST',))
event_mgmt.add_url_rule('/registration/setup/form/section/<sectionFormId>/field/<personalfield>/toggle-personal',
                        'confModifRegistrationForm-enablePersonalField',
                        rh_as_view(registrationFormModif.RHRegistrationFormModifEnablePersonalField),
                        methods=('GET', 'POST'))

# Preview
event_mgmt.add_url_rule('/registration/preview', 'confModifRegistrationPreview',
                        rh_as_view(registrationFormModif.RHRegistrationPreview))

# Registrants
event_mgmt.add_url_rule('/registration/users/', 'confModifRegistrants',
                        rh_as_view(registrantsModif.RHRegistrantListModif), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/perform-action', 'confModifRegistrants-action',
                        rh_as_view(registrantsModif.RHRegistrantListModifAction), methods=('POST',))
event_mgmt.add_url_rule('/registration/users/email/send', 'EMail-sendreg',
                        rh_as_view(registrantsModif.RHRegistrantSendEmail), methods=('POST',))
event_mgmt.add_url_rule('/registration/users/new', 'confModifRegistrants-newRegistrant',
                        rh_as_view(registrantsModif.RHRegistrantNewForm), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/remove', 'confModifRegistrants-remove',
                        rh_as_view(registrantsModif.RHRegistrantListRemove), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/', 'confModifRegistrants-modification',
                        rh_as_view(registrantsModif.RHRegistrantModification))
event_mgmt.add_url_rule('/registration/users/<registrantId>/attachments/<resId>.<fileExt>',
                        'confModifRegistrants-getAttachedFile', rh_as_view(registrantsModif.RHGetAttachedFile))
# Misc sections and personal data
event_mgmt.add_url_rule('/registration/users/<registrantId>/misc/<miscInfoId>',
                        'confModifRegistrants-modifyMiscInfo', rh_as_view(registrantsModif.RHRegistrantMiscInfoModify),
                        methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/misc/<miscInfoId>/save',
                        'confModifRegistrants-performModifyMiscInfo',
                        rh_as_view(registrantsModif.RHRegistrantMiscInfoPerformModify), methods=('POST',))
# Accommodation
event_mgmt.add_url_rule('/registration/users/<registrantId>/accommodation', 'confModifRegistrants-modifyAccommodation',
                        rh_as_view(registrantsModif.RHRegistrantAccommodationModify), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/accommodation/save',
                        'confModifRegistrants-performModifyAccommodation',
                        rh_as_view(registrantsModif.RHRegistrantAccommodationPerformModify), methods=('POST',))
# Reason for participation
event_mgmt.add_url_rule('/registration/users/<registrantId>/reasonParticipation',
                        'confModifRegistrants-modifyReasonParticipation',
                        rh_as_view(registrantsModif.RHRegistrantReasonParticipationModify), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/reasonParticipation/save',
                        'confModifRegistrants-performModifyReasonParticipation',
                        rh_as_view(registrantsModif.RHRegistrantReasonParticipationPerformModify),
                        methods=('POST',))
# Sessions
event_mgmt.add_url_rule('/registration/users/<registrantId>/sessions', 'confModifRegistrants-modifySessions',
                        rh_as_view(registrantsModif.RHRegistrantSessionModify), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/sessions/save',
                        'confModifRegistrants-performModifySessions',
                        rh_as_view(registrantsModif.RHRegistrantSessionPerformModify), methods=('POST',))
# Social events
event_mgmt.add_url_rule('/registration/users/<registrantId>/socialEvents', 'confModifRegistrants-modifySocialEvents',
                        rh_as_view(registrantsModif.RHRegistrantSocialEventsModify), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/socialEvents/save',
                        'confModifRegistrants-performModifySocialEvents',
                        rh_as_view(registrantsModif.RHRegistrantSocialEventsPerformModify), methods=('POST',))
# Statuses
event_mgmt.add_url_rule('/registration/users/<registrantId>/statuses', 'confModifRegistrants-modifyStatuses',
                        rh_as_view(registrantsModif.RHRegistrantStatusesModify), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/statuses/save',
                        'confModifRegistrants-performModifyStatuses',
                        rh_as_view(registrantsModif.RHRegistrantStatusesPerformModify), methods=('POST',))
# Payment
event_mgmt.add_url_rule('/registration/users/<registrantId>/payment', 'confModifRegistrants-modifyTransaction',
                        rh_as_view(registrantsModif.RHRegistrantTransactionModify), methods=('GET', 'POST'))
event_mgmt.add_url_rule('/registration/users/<registrantId>/payment/save',
                        'confModifRegistrants-peformModifyTransaction',
                        rh_as_view(registrantsModif.RHRegistrantTransactionPerformModify), methods=('POST',))
