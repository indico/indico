# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from indico.modules.events.registration.api import RHAPIRegistrant, RHAPIRegistrants
from indico.modules.events.registration.controllers.display import (RHRegistrationDisplayEdit, RHRegistrationFormList,
                                                                    RHRegistrationForm,
                                                                    RHRegistrationFormCheckEmail,
                                                                    RHRegistrationFormDeclineInvitation,
                                                                    RHParticipantList)
from indico.modules.events.registration.controllers.management.tickets import (RHRegistrationFormTickets,
                                                                               RHTicketDownload)
from indico.modules.events.registration.controllers.management.fields import (RHRegistrationFormToggleFieldState,
                                                                              RHRegistrationFormToggleTextState,
                                                                              RHRegistrationFormModifyField,
                                                                              RHRegistrationFormModifyText,
                                                                              RHRegistrationFormMoveField,
                                                                              RHRegistrationFormMoveText,
                                                                              RHRegistrationFormAddField,
                                                                              RHRegistrationFormAddText)
from indico.modules.events.registration.controllers.management.invitations import (RHRegistrationFormInvitations,
                                                                                   RHRegistrationFormInvite,
                                                                                   RHRegistrationFormDeleteInvitation)
from indico.modules.events.registration.controllers.management.regforms import (RHManageRegistrationForms,
                                                                                RHRegistrationFormCreate,
                                                                                RHRegistrationFormEdit,
                                                                                RHRegistrationFormDelete,
                                                                                RHRegistrationFormManage,
                                                                                RHRegistrationFormOpen,
                                                                                RHRegistrationFormClose,
                                                                                RHRegistrationFormSchedule,
                                                                                RHRegistrationFormModify)
from indico.modules.events.registration.controllers.management.sections import (RHRegistrationFormAddSection,
                                                                                RHRegistrationFormModifySection,
                                                                                RHRegistrationFormToggleSection,
                                                                                RHRegistrationFormMoveSection)
from indico.modules.events.registration.controllers.management.reglists import (RHRegistrationsListManage,
                                                                                RHRegistrationsListCustomize,
                                                                                RHRegistrationDetails,
                                                                                RHRegistrationDownloadAttachment,
                                                                                RHRegistrationEdit,
                                                                                RHRegistrationListStaticURL,
                                                                                RHRegistrationEmailRegistrants,
                                                                                RHRegistrationDelete,
                                                                                RHRegistrationCreate,
                                                                                RHRegistrationsExportPDFTable,
                                                                                RHRegistrationsExportPDFBook,
                                                                                RHRegistrationsExportCSV,
                                                                                RHRegistrationTogglePayment,
                                                                                RHRegistrationsPrintBadges)
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('event_registration', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/registration', event_feature='registration')


# Management
_bp.add_url_rule('/manage/registration/', 'manage_regform_list', RHManageRegistrationForms)
_bp.add_url_rule('/manage/registration/create', 'create_regform', RHRegistrationFormCreate, methods=('GET', 'POST'))

# Single registration form management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/', 'manage_regform', RHRegistrationFormManage)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/edit',
                 'edit_regform', RHRegistrationFormEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/delete',
                 'delete_regform', RHRegistrationFormDelete, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/open',
                 'open_regform', RHRegistrationFormOpen, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/close',
                 'close_regform', RHRegistrationFormClose, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/schedule',
                 'schedule_regform', RHRegistrationFormSchedule, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/', 'modify_regform', RHRegistrationFormModify)

# Registrations management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/', 'manage_reglist', RHRegistrationsListManage)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/customize', 'customize_reglist',
                 RHRegistrationsListCustomize, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/static-url',
                 'generate_static_url', RHRegistrationListStaticURL, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/create', 'create_registration',
                 RHRegistrationCreate, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/delete', 'delete_registrations',
                 RHRegistrationDelete, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/', 'registration_details',
                 RHRegistrationDetails)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/edit', 'edit_registration',
                 RHRegistrationEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/toggle-payment',
                 'toggle_registration_payment', RHRegistrationTogglePayment, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>'
                 '/registrations/<int:registration_id>/file/<int:field_data_id>-<filename>', 'registration_file',
                 RHRegistrationDownloadAttachment)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/email', 'email_registrants',
                 RHRegistrationEmailRegistrants, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/table.pdf',
                 'registrations_pdf_export_table', RHRegistrationsExportPDFTable, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/book.pdf',
                 'registrations_pdf_export_book', RHRegistrationsExportPDFBook, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/registrations.csv',
                 'registrations_csv_export', RHRegistrationsExportCSV, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/badges',
                 'registrations_print_badges', RHRegistrationsPrintBadges, methods=('POST',))

# Invitation management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/', 'invitations', RHRegistrationFormInvitations)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/invite', 'invite', RHRegistrationFormInvite,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/<int:invitation_id>', 'delete_invitation',
                 RHRegistrationFormDeleteInvitation, methods=('DELETE',))

# E-ticket management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/tickets', 'tickets', RHRegistrationFormTickets,
                 methods=('GET', 'POST'))

# Regform edition: sections
# The trailing slashes should be added to the blueprints here when Angular is updated
# Right now, Angular strips off trailing slashes, thus causing Flask to throw errors
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections', 'add_section', RHRegistrationFormAddSection,
                 methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>', 'modify_section',
                 RHRegistrationFormModifySection, methods=('PATCH', 'DELETE', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/toggle', 'toggle_section',
                 RHRegistrationFormToggleSection, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/move', 'move_section',
                 RHRegistrationFormMoveSection, methods=('POST',))

# Regform edition: Fields
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields', 'add_field',
                 RHRegistrationFormAddField, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields/<field_id>',
                 'modify_field', RHRegistrationFormModifyField, methods=('DELETE', 'PATCH'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields/<field_id>/toggle',
                 'toggle_field', RHRegistrationFormToggleFieldState, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields/<field_id>/move',
                 'move_field', RHRegistrationFormMoveField, methods=('POST',))

# Regform edition: Static text
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text', 'add_text',
                 RHRegistrationFormAddText, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text/<field_id>',
                 'modify_text', RHRegistrationFormModifyText, methods=('DELETE', 'PATCH'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text/<field_id>/toggle',
                 'toggle_text', RHRegistrationFormToggleTextState, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text/<field_id>/move',
                 'move_text', RHRegistrationFormMoveText, methods=('POST',))


# Display
_bp.add_url_rule('/registrations/', 'display_regform_list', RHRegistrationFormList)
_bp.add_url_rule('/registrations/participants', 'participant_list', RHParticipantList)
_bp.add_url_rule('/registrations/<int:reg_form_id>/', 'display_regform', RHRegistrationForm, methods=('GET', 'POST'))
_bp.add_url_rule('/registrations/<int:reg_form_id>/edit', 'edit_registration_display', RHRegistrationDisplayEdit,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/registrations/<int:reg_form_id>/check-email', 'check_email', RHRegistrationFormCheckEmail)
_bp.add_url_rule('/registrations/<int:reg_form_id>/decline-invitation', 'decline_invitation',
                 RHRegistrationFormDeclineInvitation, methods=('POST',))
_bp.add_url_rule('/registrations/<int:reg_form_id>/ticket.pdf', 'ticket_download', RHTicketDownload)


# API
_bp.add_url_rule('!/api/events/<event_id>/registrants/<registrant_id>', 'api_registrant',
                 RHAPIRegistrant, methods=('GET', 'PATCH'))
_bp.add_url_rule('!/api/events/<event_id>/registrants', 'api_registrants',
                 RHAPIRegistrants)
