# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.receipts.controllers import admin, event, templates
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


_bp = IndicoBlueprint('receipts', __name__, template_folder='templates', virtual_template_folder='receipts')

# Global endpoints
_bp.add_url_rule('/receipts/default-templates/<template_name>', 'get_default_template',
                 templates.RHGetDefaultTemplate)

# Global admin endpoints
_bp.add_url_rule('/admin/receipts/', 'admin_settings', admin.RHGlobalReceiptsSettings, methods=('GET', 'POST'))

_management_page = _dispatch(templates.RHEventTemplatesManagement, templates.RHCategoryTemplatesManagement)

# Endpoints available in both category and event management areas
for object_type in ('event', 'category'):
    if object_type == 'category':
        prefix = '/category/<int:category_id>'
    else:
        prefix = '/event/<int:event_id>'
    prefix += '/manage/receipts'
    defaults = {'object_type': object_type}
    # Template management pages (same RHs/backend, display routing is done in react)
    _bp.add_url_rule(f'{prefix}/', 'template_list', _management_page, defaults=defaults)
    _bp.add_url_rule(f'{prefix}/add', 'add_template_page', _management_page, defaults=defaults)
    _bp.add_url_rule(f'{prefix}/add/<template_name>', 'add_default_template', _management_page,
                     defaults=defaults)
    _bp.add_url_rule(f'{prefix}/<int:template_id>/', 'template', _management_page, defaults=defaults)
    # Add a new template
    _bp.add_url_rule(f'{prefix}/add', 'add_template', templates.RHAddTemplate, defaults=defaults, methods=('POST',))
    # Preview template while editing it
    _bp.add_url_rule(f'{prefix}/live-preview', 'template_live_preview', templates.RHLivePreview, defaults=defaults,
                     methods=('POST',))
    # Preview existing template
    _bp.add_url_rule(f'{prefix}/<int:template_id>/preview-template', 'template_preview', templates.RHPreviewTemplate,
                     defaults=defaults)
    # Update existing template
    _bp.add_url_rule(f'{prefix}/<int:template_id>/', 'edit_template', templates.RHEditTemplate, defaults=defaults,
                     methods=('PATCH',))
    # Delete template
    _bp.add_url_rule(f'{prefix}/<int:template_id>/', 'delete_template', templates.RHDeleteTemplate, defaults=defaults,
                     methods=('DELETE',))
    # Clone existing template
    _bp.add_url_rule(f'{prefix}/<int:template_id>/clone', 'clone_template', templates.RHCloneTemplate,
                     defaults=defaults, methods=('POST',))

# Receipt template operations within an event
_bp.add_url_rule('/event/<int:event_id>/manage/receipts/templates', 'all_templates', event.RHAllEventTemplates)
_bp.add_url_rule('/event/<int:event_id>/manage/receipts/images', 'images', event.RHEventImages)
_bp.add_url_rule('/event/<int:event_id>/manage/receipts/export/receipts.<any(pdf,zip):format>',
                 'receipts_export', event.RHExportReceipts, methods=('POST',))
_bp.add_url_rule('/event/<int:event_id>/manage/receipts/<int:template_id>/preview', 'receipts_preview',
                 event.RHPreviewReceipts, methods=('POST',))
_bp.add_url_rule('/event/<int:event_id>/manage/receipts/<int:template_id>/generate', 'generate_receipts',
                 event.RHGenerateReceipts, methods=('POST',))
