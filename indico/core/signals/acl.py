# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from blinker import Namespace


_signals = Namespace()


can_access = _signals.signal('can-access', """
Called when `ProtectionMixin.can_access` is used to determine if a
user can access something or not.

The `sender` is the type of the object that's using the mixin.  The
actual instance is passed as `obj`.  The `user` and `allow_admin`
arguments of `can_access` are passed as kwargs with the same name.

The `authorized` argument is ``None`` when this signal is called at
the beginning of the access check and ``True`` or ``False`` at the end
when regular access rights have already been checked.  For expensive
checks (such as anything involving database queries) it is recommended
to skip the check while `authorized` is ``None`` since the regular
access check is likely to be cheaper (due to ACLs being preloaded etc).

If the signal returns ``True`` or ``False``, the access check succeeds
or fails immediately.  If multiple subscribers to the signal return
contradictory results, ``False`` wins and access is denied.
""")


can_manage = _signals.signal('can-manage', """
Called when `ProtectionMixin.can_manage` is used to determine if a
user can manage something or not.

The `sender` is the type of the object that's using the mixin.  The
actual instance is passed as `obj`.  The `user`, `permission`,
`allow_admin`, `check_parent` and `explicit_permission` arguments of
`can_manage` are passed as kwargs with the same name.

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

If the ACL uses permissions, `old_data` will contain a dictionary of the
previous permissions (see `PrincipalPermissionsMixin.current_data`).
""")


protection_changed = _signals.signal('protection-changed', """
Called when the protection mode of an object is changed.

The `sender` is the type of the object that's using the mixin.  The
actual instance is passed as `obj`.  The old protection mode is passed
as `old_mode`, the new mode as `mode`.
""")


get_management_permissions = _signals.signal('get-management-permissions', """
Expected to return `ManagementPermission` subclasses.  The `sender` is the
type of the object the permissions may be used for.  Functions subscribing
to this signal **MUST** check the sender by specifying it using the
first argument of `connect_via()` or by comparing it inside the
function.
""")
