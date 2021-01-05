# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from indico.modules.groups.controllers import (RHGroupDelete, RHGroupDeleteMember, RHGroupDetails, RHGroupEdit,
                                               RHGroupMembers, RHGroups, RHGroupSearch)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('groups', __name__, template_folder='templates', virtual_template_folder='groups',
                      url_prefix='/admin/groups')


_bp.add_url_rule('/', 'groups', RHGroups, methods=('GET', 'POST'))
_bp.add_url_rule('/<provider>/<group_id>/', 'group_details', RHGroupDetails)
_bp.add_url_rule('/<provider>/<group_id>/members', 'group_members', RHGroupMembers)
_bp.add_url_rule('/indico/new', 'group_add', RHGroupEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/<any(indico):provider>/<int:group_id>/edit', 'group_edit', RHGroupEdit, methods=('GET', 'POST'))
_bp.add_url_rule('/<any(indico):provider>/<int:group_id>/delete', 'group_delete', RHGroupDelete, methods=('POST',))
_bp.add_url_rule('/<any(indico):provider>/<int:group_id>/<int:user_id>', 'group_delete_member', RHGroupDeleteMember,
                 methods=('DELETE',))
_bp.add_url_rule('!/groups/api/search', 'group_search', RHGroupSearch)
