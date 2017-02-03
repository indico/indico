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

from indico.modules.designer.controllers import (RHListEventTemplates, RHListCategoryTemplates, RHEditDesignerTemplate,
                                                 RHDownloadTemplateImage, RHUploadBackgroundImage,
                                                 RHDeleteDesignerTemplate, RHCloneEventTemplate, RHAddEventTemplate,
                                                 RHCloneCategoryTemplate, RHAddCategoryTemplate)
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


for object_type in ('event', 'category'):
    if object_type == 'category':
        prefix = '/category/<category_id>'
    else:
        prefix = '/event/<confId>'
    prefix += '/manage/designer'
    _bp.add_url_rule(prefix + '/', 'template_list', _dispatch(RHListEventTemplates, RHListCategoryTemplates),
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
    _bp.add_url_rule(prefix + '/<int:template_id>/images/<int:image_id>/<filename>', 'download_image',
                     RHDownloadTemplateImage, defaults={'object_type': object_type})
    _bp.add_url_rule(prefix + '/<int:template_id>/images', 'upload_image',
                     RHUploadBackgroundImage, defaults={'object_type': object_type}, methods=('POST',))
