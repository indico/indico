# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.receipts.controllers import (RHAddTemplate, RHAllCategoryTemplates, RHAllEventTemplates,
                                                 RHCategoryTemplate, RHCloneTemplate, RHDeleteTemplate, RHEditTemplate,
                                                 RHEventTemplate, RHListCategoryTemplates, RHListEventTemplates,
                                                 RHPreviewTemplate, RHPrintReceipts)
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

for object_type in ('event', 'category'):
    if object_type == 'category':
        prefix = '/category/<int:category_id>'
    else:
        prefix = '/event/<int:event_id>'
    prefix += '/manage/receipts'
    _bp.add_url_rule(prefix + '/', 'template_list', _dispatch(RHListEventTemplates, RHListCategoryTemplates),
                     defaults={'object_type': object_type})
    _bp.add_url_rule(prefix + '/add', 'add_template', RHAddTemplate,
                     defaults={'object_type': object_type}, methods=('POST',))
    _bp.add_url_rule(prefix + '/add', 'add_template_page', _dispatch(RHEventTemplate, RHCategoryTemplate),
                     defaults={'object_type': object_type}, methods=('GET',))
    _bp.add_url_rule(prefix + '/<int:template_id>/', 'template', _dispatch(RHEventTemplate, RHCategoryTemplate),
                     defaults={'object_type': object_type}, methods=('GET',))
    _bp.add_url_rule(prefix + '/<int:template_id>/preview', 'template_preview', RHPreviewTemplate,
                     defaults={'object_type': object_type}, methods=('GET',))
    _bp.add_url_rule(prefix + '/<int:template_id>/print', 'print_receipts', RHPrintReceipts,
                     defaults={'object_type': object_type}, methods=('POST',))
    _bp.add_url_rule(prefix + '/<int:template_id>/', 'edit_template', RHEditTemplate,
                     defaults={'object_type': object_type}, methods=('PATCH',))
    _bp.add_url_rule(prefix + '/<int:template_id>/', 'delete_template', RHDeleteTemplate,
                     defaults={'object_type': object_type}, methods=('DELETE',))
    _bp.add_url_rule(prefix + '/<int:template_id>/clone', 'clone_template', RHCloneTemplate,
                     defaults={'object_type': object_type}, methods=('POST',))
    _bp.add_url_rule(prefix + '/templates', 'all_templates', _dispatch(RHAllEventTemplates, RHAllCategoryTemplates),
                     defaults={'object_type': object_type}, methods=('GET',))
