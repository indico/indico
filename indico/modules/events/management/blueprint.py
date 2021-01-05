# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.events import event_management_object_url_prefixes
from indico.modules.events.management.controllers import actions, cloning, posters, program_codes, protection, settings
from indico.web.flask.util import make_compat_redirect_func
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_management', __name__, template_folder='templates',
                      virtual_template_folder='events/management',
                      url_prefix='/event/<confId>/manage')

# Settings
_bp.add_url_rule('/', 'settings', settings.RHEventSettings)
_bp.add_url_rule('/settings/data', 'edit_data', settings.RHEditEventData, methods=('GET', 'POST'))
_bp.add_url_rule('/settings/dates', 'edit_dates', settings.RHEditEventDates, methods=('GET', 'POST'))
_bp.add_url_rule('/settings/location', 'edit_location', settings.RHEditEventLocation, methods=('GET', 'POST'))
_bp.add_url_rule('/settings/persons', 'edit_persons', settings.RHEditEventPersons, methods=('GET', 'POST'))
_bp.add_url_rule('/settings/contact-info', 'edit_contact_info', settings.RHEditEventContactInfo,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/settings/classification', 'edit_classification', settings.RHEditEventClassification,
                 methods=('GET', 'POST'))
# Actions
_bp.add_url_rule('/delete', 'delete', actions.RHDeleteEvent, methods=('GET', 'POST'))
_bp.add_url_rule('/change-type', 'change_type', actions.RHChangeEventType, methods=('POST',))
_bp.add_url_rule('/lock', 'lock', actions.RHLockEvent, methods=('GET', 'POST'))
_bp.add_url_rule('/unlock', 'unlock', actions.RHUnlockEvent, methods=('POST',))
_bp.add_url_rule('/move', 'move', actions.RHMoveEvent, methods=('POST',))
# Protection
_bp.add_url_rule('/api/principals', 'api_principals', protection.RHEventPrincipals, methods=('GET', 'POST'))
_bp.add_url_rule('/api/event-roles', 'api_event_roles', protection.RHEventRolesJSON)
_bp.add_url_rule('/api/category-roles', 'api_category_roles', protection.RHCategoryRolesJSON)
_bp.add_url_rule('/protection', 'protection', protection.RHEventProtection, methods=('GET', 'POST'))
_bp.add_url_rule('/protection/acl', 'acl', protection.RHEventACL)
_bp.add_url_rule('/protection/acl-message', 'acl_message', protection.RHEventACLMessage)
_bp.add_url_rule('!/permissions-dialog/<any(event,session,contribution,category):type>', 'permissions_dialog',
                 protection.RHPermissionsDialog, methods=('POST',))
# Cloning
_bp.add_url_rule('/clone', 'clone', cloning.RHCloneEvent, methods=('GET', 'POST'))
_bp.add_url_rule('/clone/preview', 'clone_preview', cloning.RHClonePreview, methods=('GET', 'POST'))
_bp.add_url_rule('/import', 'import', cloning.RHImportFromEvent, methods=('GET', 'POST'))
_bp.add_url_rule('/import/event-details', 'import_event_details', cloning.RHImportEventDetails, methods=('POST',))
# Posters
_bp.add_url_rule('/print-poster/settings', 'poster_settings', posters.RHPosterPrintSettings, methods=('GET', 'POST'))
_bp.add_url_rule('/print-poster/<int:template_id>/<uuid>', 'print_poster', posters.RHPrintEventPoster)
# Program Codes
_bp.add_url_rule('/program-codes/', 'program_codes', program_codes.RHProgramCodes)
_bp.add_url_rule('/program-codes/templates', 'program_code_templates', program_codes.RHProgramCodeTemplates,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/program-codes/assign/sessions', 'assign_program_codes_sessions',
                 program_codes.RHAssignProgramCodesSessions, methods=('GET', 'POST'))
_bp.add_url_rule('/program-codes/assign/session-blocks', 'assign_program_codes_session_blocks',
                 program_codes.RHAssignProgramCodesSessionBlocks, methods=('GET', 'POST'))
_bp.add_url_rule('/program-codes/assign/contributions', 'assign_program_codes_contributions',
                 program_codes.RHAssignProgramCodesContributions, methods=('GET', 'POST'))
_bp.add_url_rule('/program-codes/assign/subcontributions', 'assign_program_codes_subcontributions',
                 program_codes.RHAssignProgramCodesSubContributions, methods=('GET', 'POST'))


for object_type, prefixes in event_management_object_url_prefixes.iteritems():
    if object_type == 'subcontribution':
        continue
    for prefix in prefixes:
        prefix = '!/event/<confId>' + prefix
        _bp.add_url_rule(prefix + '/show-non-inheriting', 'show_non_inheriting', protection.RHShowNonInheriting,
                         defaults={'object_type': object_type})


_compat_bp = IndicoBlueprint('compat_event_management', __name__, url_prefix='/event/<confId>/manage')
_compat_bp.add_url_rule('/general/', 'settings', make_compat_redirect_func(_bp, 'settings'))
