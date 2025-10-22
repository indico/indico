# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.
from indico.modules.email_templates.controllers import (RHAddCategoryEmailTemplate, RHAddEventEmailTemplate,
                                                        RHListCategoryEmailTemplates, RHListEventEmailTemplates,
                                                        RHEditEmailTemplate, RHDeleteEmailTemplate)
from indico.util.caching import memoize
from indico.web.flask.util import make_view_func
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('email_templates', __name__, template_folder='templates',
                      virtual_template_folder='email_templates')


@memoize
def _dispatch(event_rh, category_rh):
    event_view = make_view_func(event_rh)
    categ_view = make_view_func(category_rh)

    def view_func(**kwargs):
        return categ_view(**kwargs) if kwargs['object_type'] == 'category' else event_view(**kwargs)

    return view_func


for object_type in ('event', 'category'):
    prefix = f'/{object_type}/<int:{object_type}_id>/manage/email_templates'
    _bp.add_url_rule(f'{prefix}/', 'email_template_list',
                     _dispatch(RHListEventEmailTemplates, RHListCategoryEmailTemplates),
                     defaults={'object_type': object_type})
    _bp.add_url_rule(f'{prefix}/add', 'add_email_template',
                     _dispatch(RHAddEventEmailTemplate, RHAddCategoryEmailTemplate),
                     defaults={'object_type': object_type}, methods=('GET', 'POST'))
    _bp.add_url_rule(f'{prefix}/<int:email_template_id>/', 'edit_email_template',
                     RHEditEmailTemplate, defaults={'object_type': object_type}, methods=('GET', 'POST'))
    _bp.add_url_rule(f'{prefix}/<int:email_template_id>/', 'delete_email_template',
                     RHDeleteEmailTemplate, defaults={'object_type': object_type}, methods=('DELETE',))
    # _bp.add_url_rule(f'{prefix}/<int:email_template_id>/clone', 'clone_email_template',
    #                  _dispatch(RHCloneEventEmailTemplate, RHCloneCategoryEmailTemplate),
    #                  defaults={'object_type': object_type}, methods=('GET', 'POST'))
