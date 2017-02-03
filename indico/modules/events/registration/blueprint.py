# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
from indico.modules.events.registration.controllers.compat import compat_registration
from indico.modules.events.registration.controllers.display import (RHRegistrationDisplayEdit, RHRegistrationFormList,
                                                                    RHRegistrationForm,
                                                                    RHRegistrationFormCheckEmail,
                                                                    RHRegistrationFormDeclineInvitation,
                                                                    RHParticipantList)
from indico.modules.events.registration.controllers.management.tickets import (RHRegistrationFormTickets,
                                                                               RHTicketConfigQRCodeImage,
                                                                               RHTicketConfigQRCode,
                                                                               RHTicketDownload)
from indico.modules.events.registration.controllers.management.fields import (RHRegistrationFormToggleFieldState,
                                                                              RHRegistrationFormToggleTextState,
                                                                              RHRegistrationFormModifyField,
                                                                              RHRegistrationFormModifyText,
                                                                              RHRegistrationFormMoveField,
                                                                              RHRegistrationFormMoveText,
                                                                              RHRegistrationFormAddField,
                                                                              RHRegistrationFormAddText)
from indico.modules.events.registration.controllers.management.invitations import (
    RHRegistrationFormInvitations, RHRegistrationFormInvite, RHRegistrationFormDeleteInvitation,
    RHRegistrationFormManagerDeclineInvitation
)
from indico.modules.events.registration.controllers.management.regforms import (RHManageParticipants,
                                                                                RHManageRegistrationForms,
                                                                                RHRegistrationFormCreate,
                                                                                RHManageRegistrationFormsDisplay,
                                                                                RHRegistrationFormEdit,
                                                                                RHRegistrationFormDelete,
                                                                                RHRegistrationFormManage,
                                                                                RHRegistrationFormOpen,
                                                                                RHRegistrationFormClose,
                                                                                RHRegistrationFormSchedule,
                                                                                RHRegistrationFormModify,
                                                                                RHRegistrationFormStats,
                                                                                RHManageRegistrationFormDisplay,
                                                                                RHManageRegistrationManagers)
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
                                                                                RHRegistrationEmailRegistrantsPreview,
                                                                                RHRegistrationDelete,
                                                                                RHRegistrationCreate,
                                                                                RHRegistrationCreateMultiple,
                                                                                RHRegistrationsExportPDFTable,
                                                                                RHRegistrationsExportPDFBook,
                                                                                RHRegistrationsExportCSV,
                                                                                RHRegistrationsExportExcel,
                                                                                RHRegistrationTogglePayment,
                                                                                RHRegistrationsPrintBadges,
                                                                                RHRegistrationsConfigBadges,
                                                                                RHRegistrationApprove,
                                                                                RHRegistrationReject,
                                                                                RHRegistrationsModifyStatus,
                                                                                RHRegistrationsExportAttachments,
                                                                                RHRegistrationCheckIn,
                                                                                RHRegistrationBulkCheckIn)
from indico.web.flask.util import make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('event_registration', __name__, url_prefix='/event/<confId>', template_folder='templates',
                      virtual_template_folder='events/registration', event_feature='registration')

# Management
_bp.add_url_rule('/manage/registration/', 'manage_regform_list', RHManageRegistrationForms)
_bp.add_url_rule('/manage/registration/create', 'create_regform', RHRegistrationFormCreate, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/display', 'manage_regforms_display', RHManageRegistrationFormsDisplay,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/managers', 'manage_registration_managers', RHManageRegistrationManagers,
                 methods=('GET', 'POST'))

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
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/stats/', 'regform_stats', RHRegistrationFormStats)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/display',
                 'manage_regform_display', RHManageRegistrationFormDisplay, methods=('GET', 'POST'))

# Registrations management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/', 'manage_reglist', RHRegistrationsListManage)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/customize', 'customize_reglist',
                 RHRegistrationsListCustomize, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/static-url',
                 'generate_static_url', RHRegistrationListStaticURL, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/create', 'create_registration',
                 RHRegistrationCreate, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/create-multiple',
                 'create_multiple_registrations', RHRegistrationCreateMultiple, methods=('GET', 'POST'))
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
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/approve',
                 'approve_registration', RHRegistrationApprove, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/reject',
                 'reject_registration', RHRegistrationReject, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/check-in',
                 'registration_check_in', RHRegistrationCheckIn, methods=('PUT', 'DELETE'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/email', 'email_registrants',
                 RHRegistrationEmailRegistrants, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/email-preview', 'email_registrants_preview',
                 RHRegistrationEmailRegistrantsPreview, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/table.pdf',
                 'registrations_pdf_export_table', RHRegistrationsExportPDFTable, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/book.pdf',
                 'registrations_pdf_export_book', RHRegistrationsExportPDFBook, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/registrations.csv',
                 'registrations_csv_export', RHRegistrationsExportCSV, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/registrations.xlsx',
                 'registrations_excel_export', RHRegistrationsExportExcel, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/modify-status',
                 'registrations_modify_status', RHRegistrationsModifyStatus, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/check-in',
                 'registrations_check_in', RHRegistrationBulkCheckIn, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/attachments',
                 'registrations_attachments_export', RHRegistrationsExportAttachments, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/badges/config',
                 'registrations_config_badges', RHRegistrationsConfigBadges, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/badges/print/<int:template_id>/<uuid>',
                 'registrations_print_badges', RHRegistrationsPrintBadges)

# Invitation management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/', 'invitations', RHRegistrationFormInvitations)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/invite', 'invite', RHRegistrationFormInvite,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/<int:invitation_id>', 'delete_invitation',
                 RHRegistrationFormDeleteInvitation, methods=('DELETE',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/<int:invitation_id>/decline',
                 'manager_decline_invitation', RHRegistrationFormManagerDeclineInvitation, methods=('POST',))

# E-ticket management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/tickets', 'tickets', RHRegistrationFormTickets,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/tickets/qrcode', 'tickets_qrcode',
                 RHTicketConfigQRCode)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/tickets/qrcode.png', 'tickets_qrcode_image',
                 RHTicketConfigQRCodeImage)

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
_bp.add_url_rule('!/api/events/<int:event_id>/registrants/<int:registrant_id>', 'api_registrant',
                 RHAPIRegistrant, methods=('GET', 'PATCH'))
_bp.add_url_rule('!/api/events/<int:event_id>/registrants', 'api_registrants',
                 RHAPIRegistrants)


# Participants
_bp_participation = IndicoBlueprint('event_participation', __name__, url_prefix='/event/<confId>',
                                    template_folder='templates', virtual_template_folder='events/registration')
_bp_participation.add_url_rule('/manage/participants/', 'manage', RHManageParticipants, methods=('GET', 'POST'))


# Legacy URLs
_compat_bp = IndicoBlueprint('compat_event_registration', __name__, url_prefix='/event/<int:event_id>')
_compat_bp.add_url_rule('/registration/', 'registration', compat_registration)
_compat_bp.add_url_rule('/registration/<path:path>', 'registration', compat_registration)
_compat_bp.add_url_rule('/registration/registrants', 'registrants',
                        make_compat_redirect_func(_bp, 'participant_list', view_args_conv={'event_id': 'confId'}))
_compat_bp.add_url_rule('!/confRegistrantsDisplay.py/list', 'registrants_modpython',
                        make_compat_redirect_func(_bp, 'participant_list'))
