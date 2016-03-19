# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from blinker import Namespace

_signals = Namespace()


# legacy
access_granted = _signals.signal('access-granted', """
Called when a principal in an `AccessController` is granted access. The `sender`
is the `AccessController`; the `principal` is passed as a kwarg.
""")

access_revoked = _signals.signal('access-revoked', """
Called when a principal in an `AccessController` is revoked access. The `sender`
is the `AccessController`; the `principal` is passed as a kwarg.
""")

modification_granted = _signals.signal('modification-granted', """
Called when a principal in an `AccessController` is granted modification access. The `sender`
is the `AccessController`; the `principal` is passed as a kwarg.
""")

modification_revoked = _signals.signal('modification-revoked', """
Called when a principal in an `AccessController` is revoked modification access. The `sender`
is the `AccessController`; the `principal` is passed as a kwarg.
""")


# new
can_access = _signals.signal('can-access', """
Called when `ProtectionMixin.can_access` is used to determine if a
user can access something or not.

The `sender` is the type of the object that's using the mixin.  The
actual instance is passed as `obj`.  The `user` and `allow_admin`
arguments of `can_access` are passed as kwargs with the same name.

If the signal returns ``True`` or ``False``, the access check succeeds
or fails without any further checks.  If multiple subscribers to the
signal return contradictory results, ``False`` wins and access is
denied.
""")


can_manage = _signals.signal('can-manage', """
Called when `ProtectionMixin.can_manage` is used to determine if a
user can manage something or not.

The `sender` is the type of the object that's using the mixin.  The
actual instance is passed as `obj`.  The `user`, `role`, `allow_admin`,
`check_parent` and `explicit_role` arguments of `can_manage` are
passed as kwargs with the same name.

If the signal returns ``True`` or ``False``, the access check succeeds
or fails without any further checks.  If multiple subscribers to the
signal return contradictory results, ``False`` wins and access is
denied.
""")


entry_changed = _signals.signal('entry-changed', """
Called when an ACL entry is changed.

The `sender` is the type of the object that's using the mixin.  The
actual instance is passed as `obj`.  The `User`, `GroupProxy` or
`EmailPrincipal` is passed as `principal` and `entry` contains the
actual ACL entry (a `PrincipalMixin` instance) or ``None`` in case
the entry was deleted.  `is_new` is a boolean indicating whether
the given principal was in the ACL before.  If `quiet` is ``True``,
signal handlers should not perform noisy actions such as logging or
sending emails related to the change.

If the ACL uses roles, `old_data` will contain a dictionary of the
previous roles/permissions (see `PrincipalRolesMixin.current_data`).
""")


get_management_roles = _signals.signal('get-management-roles', """
Expected to return `ManagementRole` subclasses.  The `sender` is the
type of the object the roles may be used for.  Functions subscribing
to this signal **MUST** check the sender by specifying it using the
first argument of `connect_via()` or by comparing it inside the
function.
""")
