# This file is part of Indico.
# Copyright (C) 2002 - 2022 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.registration import api
from indico.modules.events.registration.controllers import display
from indico.modules.events.registration.controllers.compat import compat_registration
from indico.modules.events.registration.controllers.management import (fields, invitations, privacy, regforms, reglists,
                                                                       sections, tags, tickets)
from indico.web.flask.util import make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_registration', __name__, url_prefix='/event/<int:event_id>', template_folder='templates',
                      virtual_template_folder='events/registration', event_feature='registration')

# Management
_bp.add_url_rule('/manage/registration/', 'manage_regform_list', regforms.RHManageRegistrationForms)
_bp.add_url_rule('/manage/registration/create', 'create_regform', regforms.RHRegistrationFormCreate,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/display', 'manage_regforms_display', regforms.RHManageRegistrationFormsDisplay,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/managers', 'manage_registration_managers', regforms.RHManageRegistrationManagers,
                 methods=('GET', 'POST'))

# Single registration form management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/', 'manage_regform', regforms.RHRegistrationFormManage)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/edit', 'edit_regform', regforms.RHRegistrationFormEdit,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/delete', 'delete_regform', regforms.RHRegistrationFormDelete,
                 methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/open', 'open_regform', regforms.RHRegistrationFormOpen,
                 methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/close', 'close_regform', regforms.RHRegistrationFormClose,
                 methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/schedule', 'schedule_regform',
                 regforms.RHRegistrationFormSchedule, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/', 'modify_regform', regforms.RHRegistrationFormModify)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/stats/', 'regform_stats', regforms.RHRegistrationFormStats)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/display', 'manage_regform_display',
                 regforms.RHManageRegistrationFormDisplay, methods=('GET', 'POST'))

# Registrations management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/', 'manage_reglist',
                 reglists.RHRegistrationsListManage)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/customize', 'customize_reglist',
                 reglists.RHRegistrationsListCustomize, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/static-url', 'generate_static_url',
                 reglists.RHRegistrationListStaticURL, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/create', 'create_registration',
                 reglists.RHRegistrationCreate, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/create-multiple',
                 'create_multiple_registrations', reglists.RHRegistrationCreateMultiple, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/delete', 'delete_registrations',
                 reglists.RHRegistrationDelete, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/', 'registration_details',
                 reglists.RHRegistrationDetails)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/edit', 'edit_registration',
                 reglists.RHRegistrationEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/toggle-payment',
                 'toggle_registration_payment', reglists.RHRegistrationTogglePayment, methods=('POST',))
_bp.add_url_rule(
    '/manage/registration/<int:reg_form_id>' '/registrations/<int:registration_id>/file/<int:field_data_id>-<filename>',
    'registration_file', reglists.RHRegistrationDownloadAttachment)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/approve',
                 'approve_registration', reglists.RHRegistrationApprove, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/reject',
                 'reject_registration', reglists.RHRegistrationReject, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/reset',
                 'reset_registration', reglists.RHRegistrationReset, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/hide',
                 'hide_registration', reglists.RHRegistrationHide, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/withdraw',
                 'manage_withdraw_registration', reglists.RHRegistrationManageWithdraw, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/<int:registration_id>/check-in',
                 'registration_check_in', reglists.RHRegistrationCheckIn, methods=('PUT', 'DELETE'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/email', 'email_registrants',
                 reglists.RHRegistrationEmailRegistrants, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/email-preview', 'email_registrants_preview',
                 reglists.RHRegistrationEmailRegistrantsPreview, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/import', 'registrations_import',
                 reglists.RHRegistrationsImport, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/table.pdf', 'registrations_pdf_export_table',
                 reglists.RHRegistrationsExportPDFTable, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/book.pdf', 'registrations_pdf_export_book',
                 reglists.RHRegistrationsExportPDFBook, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/registrations.csv', 'registrations_csv_export',
                 reglists.RHRegistrationsExportCSV, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/registrations.xlsx',
                 'registrations_excel_export', reglists.RHRegistrationsExportExcel, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/approve', 'registrations_approve',
                 reglists.RHRegistrationsApprove, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/reject', 'registrations_reject',
                 reglists.RHRegistrationsReject, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/check-in', 'registrations_check_in',
                 reglists.RHRegistrationBulkCheckIn, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/registrations/attachments', 'registrations_attachments_export',
                 reglists.RHRegistrationsExportAttachments, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/badges/config', 'registrations_config_badges',
                 reglists.RHRegistrationsConfigBadges, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/tickets/config', 'registrations_config_tickets',
                 reglists.RHRegistrationsConfigTickets, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/badges/print/<int:template_id>/<uuid>',
                 'registrations_print_badges', reglists.RHRegistrationsPrintBadges)

# Invitation management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/', 'invitations',
                 invitations.RHRegistrationFormInvitations)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/invite', 'invite',
                 invitations.RHRegistrationFormInvite, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/import', 'import',
                 invitations.RHRegistrationFormInviteImport, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/<int:invitation_id>', 'delete_invitation',
                 invitations.RHRegistrationFormDeleteInvitation, methods=('DELETE',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/invitations/<int:invitation_id>/decline',
                 'manager_decline_invitation', invitations.RHRegistrationFormManagerDeclineInvitation,
                 methods=('POST',))

# E-ticket management
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/tickets', 'tickets', tickets.RHRegistrationFormTickets,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/tickets/qrcode', 'tickets_qrcode',
                 tickets.RHTicketConfigQRCode)
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/tickets/qrcode.png', 'tickets_qrcode_image',
                 tickets.RHTicketConfigQRCodeImage)

# Registration tag management
_bp.add_url_rule('/manage/registration/tags', 'manage_registration_tags', tags.RHManageRegistrationTags,
                 methods=('GET',))
_bp.add_url_rule('/manage/registration/tags/add', 'manage_registration_tags_add',
                 tags.RHRegistrationTagAdd, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/tags/<int:tag_id>/edit', 'manage_registration_tags_edit',
                 tags.RHRegistrationTagEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/manage/registration/tags/<int:tag_id>/delete', 'manage_registration_tags_delete',
                 tags.RHRegistrationTagDelete, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/tags/assign', 'manage_registration_tags_assign',
                 tags.RHRegistrationTagsAssign, methods=('POST',))

# Regform edition: sections
# The trailing slashes should be added to the blueprints here when Angular is updated
# Right now, Angular strips off trailing slashes, thus causing Flask to throw errors
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections', 'add_section',
                 sections.RHRegistrationFormAddSection, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>', 'modify_section',
                 sections.RHRegistrationFormModifySection, methods=('PATCH', 'DELETE', 'POST'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/toggle', 'toggle_section',
                 sections.RHRegistrationFormToggleSection, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/move', 'move_section',
                 sections.RHRegistrationFormMoveSection, methods=('POST',))

# Regform edition: Fields
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields', 'add_field',
                 fields.RHRegistrationFormAddField, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields/<field_id>',
                 'modify_field', fields.RHRegistrationFormModifyField, methods=('DELETE', 'PATCH'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields/<field_id>/toggle',
                 'toggle_field', fields.RHRegistrationFormToggleFieldState, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields/<field_id>/move',
                 'move_field', fields.RHRegistrationFormMoveField, methods=('POST',))

# Regform edition: Static text
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text', 'add_text',
                 fields.RHRegistrationFormAddText, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text/<field_id>',
                 'modify_text', fields.RHRegistrationFormModifyText, methods=('DELETE', 'PATCH'))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text/<field_id>/toggle',
                 'toggle_text', fields.RHRegistrationFormToggleTextState, methods=('POST',))
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text/<field_id>/move',
                 'move_text', fields.RHRegistrationFormMoveText, methods=('POST',))


# Display
_bp.add_url_rule('/registrations/', 'display_regform_list', display.RHRegistrationFormList)
_bp.add_url_rule('/registrations/participants', 'participant_list', display.RHParticipantList)
_bp.add_url_rule('/registrations/<int:reg_form_id>/', 'display_regform', display.RHRegistrationForm,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/registrations/<int:reg_form_id>/upload', 'upload_registration_file',
                 display.RHUploadRegistrationFile, methods=('POST',))
_bp.add_url_rule('/registrations/<int:reg_form_id>/edit', 'edit_registration_display',
                 display.RHRegistrationDisplayEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/registrations/<int:reg_form_id>/withdraw', 'withdraw_registration',
                 display.RHRegistrationWithdraw, methods=('POST',))
_bp.add_url_rule('/registrations/<int:reg_form_id>/check-email', 'check_email', display.RHRegistrationFormCheckEmail)
_bp.add_url_rule('/registrations/<int:reg_form_id>/decline-invitation', 'decline_invitation',
                 display.RHRegistrationFormDeclineInvitation, methods=('POST',))
_bp.add_url_rule('/registrations/<int:reg_form_id>/ticket.pdf', 'ticket_download', display.RHTicketDownload)
_bp.add_url_rule('/registrations/<int:reg_form_id>/<int:registration_id>/avatar', 'registration_avatar',
                 display.RHRegistrationAvatar)


# API
_bp.add_url_rule('!/api/events/<int:event_id>/registrants/<int:registrant_id>', 'api_registrant',
                 api.RHAPIRegistrant, methods=('GET', 'PATCH'))
_bp.add_url_rule('!/api/events/<int:event_id>/registrants', 'api_registrants',
                 api.RHAPIRegistrants)
_bp.add_url_rule('/api/registration-forms', 'api_registration_forms', api.RHAPIRegistrationForms)
_bp.add_url_rule('/api/registration/<int:reg_form_id>/tags/assign', 'api_registration_tags_assign',
                 tags.RHAPIRegistrationTagsAssign, methods=('POST',))
_bp.add_url_rule('/api/registration/<int:reg_form_id>/privacy/consent', 'api_registration_change_consent',
                 privacy.RHAPIRegistrationChangeConsent, methods=('POST',))

# Participants
_bp_participation = IndicoBlueprint('event_participation', __name__, url_prefix='/event/<int:event_id>',
                                    template_folder='templates', virtual_template_folder='events/registration')
_bp_participation.add_url_rule('/manage/participants/', 'manage', regforms.RHManageParticipants,
                               methods=('GET', 'POST'))

# Privacy
_bp.add_url_rule('/manage/registration/<int:reg_form_id>/privacy/settings', 'manage_registration_privacy_settings',
                 privacy.RHRegistrationPrivacy, methods=('GET', 'POST'))

# Legacy URLs
_compat_bp = IndicoBlueprint('compat_event_registration', __name__, url_prefix='/event/<int:event_id>')
_compat_bp.add_url_rule('/registration/', 'registration', compat_registration)
_compat_bp.add_url_rule('/registration/<path:path>', 'registration', compat_registration)
_compat_bp.add_url_rule('/registration/registrants', 'registrants', make_compat_redirect_func(_bp, 'participant_list'))
_compat_bp.add_url_rule('!/confRegistrantsDisplay.py/list', 'registrants_modpython',
                        make_compat_redirect_func(_bp, 'participant_list'))
