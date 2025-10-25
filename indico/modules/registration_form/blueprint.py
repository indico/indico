# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.categories.registration.controllers import fields as category_fields
from indico.modules.categories.registration.controllers import privacy as category_privacy
from indico.modules.categories.registration.controllers import regforms as category_regforms
from indico.modules.categories.registration.controllers import sections as category_sections
from indico.modules.events.registration.controllers.management import fields as event_fields
from indico.modules.events.registration.controllers.management import privacy as event_privacy
from indico.modules.events.registration.controllers.management import regforms as event_regforms
from indico.modules.events.registration.controllers.management import sections as event_sections
from indico.modules.registration_form.controllers.api import misc as api_misc
from indico.util.caching import memoize
from indico.web.flask.util import make_view_func
from indico.web.flask.wrappers import IndicoBlueprint


@memoize
def _dispatch(event_rh, category_rh):
    event_view = make_view_func(event_rh)
    categ_view = make_view_func(category_rh)

    def view_func(**kwargs):
        return categ_view(**kwargs) if kwargs['object_type'] == 'category' else event_view(**kwargs)

    return view_func


_bp = IndicoBlueprint('registration_form', __name__, template_folder='templates',
                      virtual_template_folder='registration_form', event_feature='registration')


# Endpoints available in both category and event management areas
for object_type in ('event', 'category'):
    prefix = '/category/<int:category_id>' if object_type == 'category' else '/event/<int:event_id>'
    defaults = {'object_type': object_type}

    _bp.add_url_rule(f'{prefix}/manage/registration/', 'manage_regform_list',
                     _dispatch(event_regforms.RHEventManageRegistrationForms,
                     category_regforms.RHCategoryManageRegistrationForms),
                     defaults=defaults)
    _bp.add_url_rule(f'{prefix}/manage/registration/create', 'create_regform',
                     _dispatch(event_regforms.RHEventRegistrationFormCreate,
                     category_regforms.RHCategoryRegistrationFormCreate),
                     defaults=defaults, methods=('GET', 'POST'))
    _bp.add_url_rule(f'{prefix}/manage/registration/<int:reg_form_id>/', 'manage_regform',
                     _dispatch(event_regforms.RHEventRegistrationFormManage,
                     category_regforms.RHCategoryRegistrationFormManage),
                     defaults=defaults)
    # Single registration form management
    _bp.add_url_rule(f'{prefix}/manage/registration/<int:reg_form_id>/edit', 'edit_regform',
                     _dispatch(event_regforms.RHEventRegistrationFormEdit,
                     category_regforms.RHCategoryRegistrationFormEdit),
                     methods=('GET', 'POST'), defaults=defaults)
    _bp.add_url_rule(f'{prefix}/manage/registration/<int:reg_form_id>/delete', 'delete_regform',
                     _dispatch(event_regforms.RHEventRegistrationFormDelete,
                     category_regforms.RHCategoryRegistrationFormDelete),
                     methods=('POST',), defaults=defaults)
    _bp.add_url_rule(f'{prefix}/manage/registration/<int:reg_form_id>/form/', 'modify_regform',
                     _dispatch(event_regforms.RHEventRegistrationFormModify,
                     category_regforms.RHCategoryRegistrationFormModify),
                     defaults=defaults)

    # Privacy
    _bp.add_url_rule(f'{prefix}/manage/registration/<int:reg_form_id>/privacy/settings',
                     'manage_registration_privacy_settings',
                     _dispatch(event_privacy.RHEventRegistrationPrivacy,
                               category_privacy.RHCategoryRegistrationPrivacy),
                     methods=('GET', 'POST'), defaults=defaults)

    # Regform edition: sections
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections', 'add_section',
        _dispatch(event_sections.RHEventRegistrationFormAddSection,
                  category_sections.RHCategoryRegistrationFormAddSection),
        defaults=defaults, methods=('POST',))
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>', 'modify_section',
        _dispatch(event_sections.RHEventRegistrationFormModifySection,
                  category_sections.RHCategoryRegistrationFormModifySection),
        defaults=defaults, methods=('PATCH', 'DELETE', 'POST'))
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>/toggle', 'toggle_section',
        _dispatch(event_sections.RHEventRegistrationFormToggleSection,
                  category_sections.RHCategoryRegistrationFormToggleSection),
        defaults=defaults, methods=('POST',))
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>/move', 'move_section',
        _dispatch(event_sections.RHEventRegistrationFormMoveSection,
                  category_sections.RHCategoryRegistrationFormMoveSection),
        defaults=defaults, methods=('POST',))

    # Regform edition: Fields
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields', 'add_field',
        _dispatch(event_fields.RHEventRegistrationFormAddField, category_fields.RHCategoryRegistrationFormAddField),
        defaults=defaults, methods=('POST',))
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields/<field_id>', 'modify_field',
        _dispatch(event_fields.RHEventRegistrationFormModifyField,
                  category_fields.RHCategoryRegistrationFormModifyField),
        defaults=defaults, methods=('DELETE', 'PATCH'))
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields/<field_id>/toggle',
        'toggle_field',
        _dispatch(event_fields.RHEventRegistrationFormToggleFieldState,
                  category_fields.RHCategoryRegistrationFormToggleFieldState),
        defaults=defaults, methods=('POST',))
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>/fields/<field_id>/move',
        'move_field',
        _dispatch(event_fields.RHEventRegistrationFormMoveField, category_fields.RHCategoryRegistrationFormMoveField),
        defaults=defaults, methods=('POST',))

    # Regform edition: Static text
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text', 'add_text',
        _dispatch(event_fields.RHEventRegistrationFormAddText, category_fields.RHCategoryRegistrationFormAddText),
        defaults=defaults, methods=('POST',))
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text/<field_id>', 'modify_text',
        _dispatch(event_fields.RHEventRegistrationFormModifyText, category_fields.RHCategoryRegistrationFormModifyText),
         defaults=defaults, methods=('DELETE', 'PATCH'))
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text/<field_id>/toggle',
        'toggle_text',
        _dispatch(event_fields.RHEventRegistrationFormToggleTextState,
                  category_fields.RHCategoryRegistrationFormToggleTextState),
         defaults=defaults, methods=('POST',))
    _bp.add_url_rule(
        f'{prefix}/manage/registration/<int:reg_form_id>/form/sections/<section_id>/text/<field_id>/move', 'move_text',
        _dispatch(event_fields.RHEventRegistrationFormMoveText, category_fields.RHCategoryRegistrationFormMoveText),
         defaults=defaults, methods=('POST',))

event_url_prefix = '/event/<int:event_id>'
_bp.add_url_rule(f'{event_url_prefix}/api/regform-template-list', 'regform_template_list',
                api_misc.RHListTemplateRegistrationForms, methods=('POST',))
