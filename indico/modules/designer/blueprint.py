# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.designer.controllers import (RHAddCategoryTemplate, RHAddEventTemplate, RHCloneCategoryTemplate,
                                                 RHCloneEventTemplate, RHDeleteDesignerTemplate,
                                                 RHDownloadTemplateImage, RHEditDesignerTemplate, RHGetTemplateData,
                                                 RHListBacksideTemplates, RHListCategoryTemplates, RHListEventTemplates,
                                                 RHToggleBadgeDefaultOnCategory, RHToggleTicketDefaultOnCategory,
                                                 RHUploadBackgroundImage)
from indico.util.caching import memoize
from indico.web.flask.util import make_view_func
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('designer', __name__, template_folder='templates', virtual_template_folder='designer')


@memoize
def _dispatch(event_rh, category_rh):
    event_view = make_view_func(event_rh)
    categ_view = make_view_func(category_rh)

    def view_func(**kwargs):
        return categ_view(**kwargs) if kwargs['object_type'] == 'category' else event_view(**kwargs)

    return view_func


_bp.add_url_rule('/category/<int:category_id>/manage/designer/<int:template_id>/toggle-default-ticket',
                 'toggle_category_default_ticket', RHToggleTicketDefaultOnCategory, methods=('POST',))
_bp.add_url_rule('/category/<int:category_id>/manage/designer/<int:template_id>/toggle-default-badge',
                 'toggle_category_default_badge', RHToggleBadgeDefaultOnCategory, methods=('POST',))


for object_type in ('event', 'category'):
    if object_type == 'category':
        prefix = '/category/<int:category_id>'
    else:
        prefix = '/event/<int:confId>'
    prefix += '/manage/designer'
    _bp.add_url_rule(prefix + '/', 'template_list', _dispatch(RHListEventTemplates, RHListCategoryTemplates),
                     defaults={'object_type': object_type})
    _bp.add_url_rule(prefix + '/<int:template_id>/backsides', 'backside_template_list', RHListBacksideTemplates,
                     defaults={'object_type': object_type})
    _bp.add_url_rule(prefix + '/add', 'add_template', _dispatch(RHAddEventTemplate, RHAddCategoryTemplate),
                     defaults={'object_type': object_type}, methods=('GET', 'POST'))
    _bp.add_url_rule(prefix + '/<int:template_id>/', 'edit_template', RHEditDesignerTemplate,
                     defaults={'object_type': object_type}, methods=('GET', 'POST'))
    _bp.add_url_rule(prefix + '/<int:template_id>/', 'delete_template', RHDeleteDesignerTemplate,
                     defaults={'object_type': object_type}, methods=('DELETE',))
    _bp.add_url_rule(prefix + '/<int:template_id>/clone', 'clone_template',
                     _dispatch(RHCloneEventTemplate, RHCloneCategoryTemplate),
                     defaults={'object_type': object_type}, methods=('POST',))
    _bp.add_url_rule(prefix + '/<int:template_id>/data', 'get_template_data',
                     RHGetTemplateData, defaults={'object_type': object_type})
    _bp.add_url_rule(prefix + '/<int:template_id>/images/<int:image_id>/<filename>', 'download_image',
                     RHDownloadTemplateImage, defaults={'object_type': object_type})
    _bp.add_url_rule(prefix + '/<int:template_id>/images', 'upload_image',
                     RHUploadBackgroundImage, defaults={'object_type': object_type}, methods=('POST',))
