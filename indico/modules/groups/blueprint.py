# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from indico.modules.groups.controllers import (RHGroupDelete, RHGroupDeleteMember, RHGroupDetails, RHGroupEdit,
                                               RHGroupMembers, RHGroups)
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
