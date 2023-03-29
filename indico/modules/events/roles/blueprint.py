# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.modules.events.roles.controllers import (RHAddEventRole, RHAddEventRoleMembers, RHDeleteEventRole,
                                                     RHEditEventRole, RHEventRoleMembersExportCSV,
                                                     RHEventRoleMembersImportCSV, RHEventRoles, RHEventRolesAPI,
                                                     RHRemoveEventRoleMember)
from indico.web.flask.wrappers import IndicoBlueprint


_bp = IndicoBlueprint('event_roles', __name__, template_folder='templates', virtual_template_folder='events/roles',
                      url_prefix='/event/<int:event_id>/manage/roles')

_bp.add_url_rule('/', 'manage', RHEventRoles)
_bp.add_url_rule('/create', 'add_role', RHAddEventRole, methods=('GET', 'POST'))

_bp.add_url_rule('/<int:role_id>/edit', 'edit_role', RHEditEventRole, methods=('GET', 'POST'))
_bp.add_url_rule('/<int:role_id>', 'delete_role', RHDeleteEventRole, methods=('DELETE',))

_bp.add_url_rule('/<int:role_id>/members', 'add_role_members', RHAddEventRoleMembers, methods=('POST',))
_bp.add_url_rule('/<int:role_id>/members/<int:user_id>', 'remove_role_member', RHRemoveEventRoleMember,
                 methods=('DELETE',))

_bp.add_url_rule('/<int:role_id>/members/import', 'add_members_import_csv', RHEventRoleMembersImportCSV,
                 methods=('GET', 'POST'))
_bp.add_url_rule('/<int:role_id>/members.csv', 'members_export_csv', RHEventRoleMembersExportCSV)

# API
_bp.add_url_rule('/api/roles/', 'api_roles', RHEventRolesAPI)
