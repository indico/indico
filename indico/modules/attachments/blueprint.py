# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

import itertools

from indico.modules.attachments.controllers.compat import (RHCompatAttachmentNew, compat_attachment, compat_folder,
                                                           compat_folder_old)
from indico.modules.attachments.controllers.display.category import RHDownloadCategoryAttachment
from indico.modules.attachments.controllers.display.event import (RHDownloadEventAttachment,
                                                                  RHListEventAttachmentFolder,
                                                                  RHPackageEventAttachmentsDisplay)
from indico.modules.attachments.controllers.event_package import RHPackageEventAttachmentsStatus
from indico.modules.attachments.controllers.management.category import (RHAddCategoryAttachmentFiles,
                                                                        RHAddCategoryAttachmentLink,
                                                                        RHCreateCategoryFolder,
                                                                        RHDeleteCategoryAttachment,
                                                                        RHDeleteCategoryFolder,
                                                                        RHEditCategoryAttachment, RHEditCategoryFolder,
                                                                        RHManageCategoryAttachments)
from indico.modules.attachments.controllers.management.event import (RHAddEventAttachmentFiles,
                                                                     RHAddEventAttachmentLink,
                                                                     RHAttachmentManagementInfoColumn,
                                                                     RHCreateEventFolder, RHDeleteEventAttachment,
                                                                     RHDeleteEventFolder, RHEditEventAttachment,
                                                                     RHEditEventFolder, RHManageEventAttachments,
                                                                     RHPackageEventAttachmentsManagement)
from indico.modules.events import event_management_object_url_prefixes, event_object_url_prefixes
from indico.util.caching import memoize
from indico.web.flask.util import make_compat_redirect_func, make_view_func
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('attachments', __name__, template_folder='templates', virtual_template_folder='attachments')


@memoize
def _dispatch(event_rh, category_rh):
    event_view = make_view_func(event_rh)
    categ_view = make_view_func(category_rh)

    def view_func(**kwargs):
        return categ_view(**kwargs) if kwargs['object_type'] == 'category' else event_view(**kwargs)

    return view_func


# Management
items = itertools.chain(event_management_object_url_prefixes.iteritems(), [('category', ['/manage'])])
for object_type, prefixes in items:
    for prefix in prefixes:
        if object_type == 'category':
            prefix = '/category/<int:category_id>' + prefix
        else:
            prefix = '/event/<int:confId>' + prefix
        _bp.add_url_rule(prefix + '/attachments/', 'management',
                         _dispatch(RHManageEventAttachments, RHManageCategoryAttachments),
                         defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/attachments/info-column', 'management_info_column',
                         RHAttachmentManagementInfoColumn,
                         defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/attachments/add/files', 'upload',
                         _dispatch(RHAddEventAttachmentFiles, RHAddCategoryAttachmentFiles),
                         methods=('GET', 'POST'), defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/attachments/add/link', 'add_link',
                         _dispatch(RHAddEventAttachmentLink, RHAddCategoryAttachmentLink),
                         methods=('GET', 'POST'), defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/attachments/<int:folder_id>/<int:attachment_id>/', 'modify_attachment',
                         _dispatch(RHEditEventAttachment, RHEditCategoryAttachment),
                         methods=('GET', 'POST'), defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/attachments/create-folder', 'create_folder',
                         _dispatch(RHCreateEventFolder, RHCreateCategoryFolder),
                         methods=('GET', 'POST'), defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/attachments/<int:folder_id>/', 'edit_folder',
                         _dispatch(RHEditEventFolder, RHEditCategoryFolder),
                         methods=('GET', 'POST'), defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/attachments/<int:folder_id>/', 'delete_folder',
                         _dispatch(RHDeleteEventFolder, RHDeleteCategoryFolder),
                         methods=('DELETE',), defaults={'object_type': object_type})
        _bp.add_url_rule(prefix + '/attachments/<int:folder_id>/<int:attachment_id>/', 'delete_attachment',
                         _dispatch(RHDeleteEventAttachment, RHDeleteCategoryAttachment),
                         methods=('DELETE',), defaults={'object_type': object_type})

# Display/download
items = itertools.chain(event_object_url_prefixes.iteritems(), [('category', [''])])
for object_type, prefixes in items:
    for prefix in prefixes:
        if object_type == 'category':
            prefix = '/category/<category_id>' + prefix
        else:
            prefix = '/event/<confId>' + prefix
        _bp.add_url_rule(prefix + '/attachments/<int:folder_id>/<int:attachment_id>/<filename>', 'download',
                         _dispatch(RHDownloadEventAttachment, RHDownloadCategoryAttachment),
                         defaults={'object_type': object_type})

        # attachments folders cannot be consulted in categories
        if object_type != 'category':
            _bp.add_url_rule(prefix + '/attachments/<int:folder_id>/', 'list_folder',
                             RHListEventAttachmentFolder,
                             defaults={'object_type': object_type})


# Package
_bp.add_url_rule('/event/<confId>/attachments/package', 'package',
                 RHPackageEventAttachmentsDisplay, methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/manage/attachments/package', 'package_management',
                 RHPackageEventAttachmentsManagement, methods=('GET', 'POST'))
_bp.add_url_rule('/event/<confId>/attachments/package/status/<task_id>', 'package_status',
                 RHPackageEventAttachmentsStatus)


# Legacy redirects for the old URLs
_compat_bp = IndicoBlueprint('compat_attachments', __name__, url_prefix='/event/<event_id>')
compat_folder_rules = [
    '/material/<material_id>/',
    '/session/<session_id>/contribution/<contrib_id>/material/<material_id>/',
    '/contribution/<contrib_id>/material/<material_id>/'
]
compat_attachment_rules = [
    '/material/<material_id>/<resource_id>',
    '/material/<material_id>/<resource_id>.<ext>',
    '/session/<session_id>/material/<material_id>/<resource_id>',
    '/session/<session_id>/material/<material_id>/<resource_id>.<ext>',
    '/session/<session_id>/contribution/<contrib_id>/material/<material_id>/<resource_id>',
    '/session/<session_id>/contribution/<contrib_id>/material/<material_id>/<resource_id>.<ext>',
    '/session/<session_id>/contribution/<contrib_id>/<subcontrib_id>/material/<material_id>/<resource_id>',
    '/session/<session_id>/contribution/<contrib_id>/<subcontrib_id>/material/<material_id>/<resource_id>.<ext>',
    '/contribution/<contrib_id>/material/<material_id>/<resource_id>',
    '/contribution/<contrib_id>/material/<material_id>/<resource_id>.<ext>',
    '/contribution/<contrib_id>/<subcontrib_id>/material/<material_id>/<resource_id>',
    '/contribution/<contrib_id>/<subcontrib_id>/material/<material_id>/<resource_id>.<ext>'
]
old_obj_prefix_rules = {
    'session': ['!/event/<confId>/session/<sessionId>'],
    'contribution': ['!/event/<confId>/session/<sessionId>/contribution/<contribId>',
                     '!/event/<confId>/contribution/<contribId>'],
    'subcontribution': ['!/event/<confId>/session/<sessionId>/contribution/<contribId>/<subContId>',
                        '!/event/<confId>/contribution/<contribId>/<subContId>']
}
for rule in compat_folder_rules:
    _compat_bp.add_url_rule(rule, 'folder', compat_folder)
for rule in compat_attachment_rules:
    _compat_bp.add_url_rule(rule, 'attachment', compat_attachment)
for object_type, prefixes in old_obj_prefix_rules.iteritems():
    for prefix in prefixes:
        # we rely on url normalization to redirect to the proper URL for the object
        _compat_bp.add_url_rule(prefix + '/attachments/<int:folder_id>/<int:attachment_id>/<filename>',
                                'compat_download', RHCompatAttachmentNew, defaults={'object_type': object_type})

_compat_bp.add_url_rule('!/getFile.py/access', 'getfile',
                        make_compat_redirect_func(_compat_bp, 'attachment',
                                                  view_args_conv={'confId': 'event_id',
                                                                  'sessionId': 'session_id',
                                                                  'contribId': 'contrib_id',
                                                                  'subContId': 'subcontrib_id',
                                                                  'materialId': 'material_id',
                                                                  'resId': 'resource_id'}))
_compat_bp.add_url_rule('!/materialDisplay.py', 'materialdisplay', compat_folder_old)
