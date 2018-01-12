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

from indico.modules.events.roles.controllers import (RHAddEventRole, RHAddEventRoleMembers, RHDeleteEventRole,
                                                     RHEditEventRole, RHEventRoles, RHRemoveEventRoleMember)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_roles', __name__, template_folder='templates', virtual_template_folder='events/roles',
                      url_prefix='/event/<confId>/manage/roles')

_bp.add_url_rule('/', 'manage', RHEventRoles)
_bp.add_url_rule('/create', 'add_role', RHAddEventRole, methods=('GET', 'POST'))

_bp.add_url_rule('/<int:role_id>/edit', 'edit_role', RHEditEventRole, methods=('GET', 'POST'))
_bp.add_url_rule('/<int:role_id>', 'delete_role', RHDeleteEventRole, methods=('DELETE',))

_bp.add_url_rule('/<int:role_id>/members', 'add_members', RHAddEventRoleMembers, methods=('POST',))
_bp.add_url_rule('/<int:role_id>/members/<int:user_id>', 'remove_member', RHRemoveEventRoleMember, methods=('DELETE',))
