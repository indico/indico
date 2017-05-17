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

import pytest

from indico.modules.rb import rb_settings
from indico.modules.rb.util import rb_is_admin, rb_check_user_access
from indico.testing.util import bool_matrix


@pytest.mark.parametrize(('is_rb_admin', 'acl_empty', 'in_acl', 'expected'), bool_matrix('...', expect=any))
def test_rb_check_user_access(db, mocker, dummy_user, dummy_group, is_rb_admin, acl_empty, in_acl, expected):
    if is_rb_admin:
        mocker.patch('indico.modules.rb.util.rb_is_admin', return_value=True)
    if not acl_empty:
        rb_settings.acls.add_principal('authorized_principals', dummy_group)
    if in_acl:
        rb_settings.acls.add_principal('authorized_principals', dummy_user)
    assert rb_check_user_access(dummy_user) == expected


@pytest.mark.parametrize(('is_admin', 'is_rb_admin', 'expected'), bool_matrix('..', expect=any))
def test_rb_is_admin(create_user, is_admin, is_rb_admin, expected):
    user = create_user(1, admin=is_admin, rb_admin=is_rb_admin)
    assert rb_is_admin(user) == expected
