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

import pytest

from indico.core.db.sqlalchemy.protection import ProtectionMode


@pytest.mark.parametrize(('protection_mode', 'creation_restricted', 'acl', 'allowed'), (
    # not restricted
    (ProtectionMode.public, False, None, True),
    (ProtectionMode.protected, False, None, False),
    (ProtectionMode.protected, False, {'read_access': True}, True),
    # restricted - authorized
    (ProtectionMode.protected, True, {'full_access': True}, True),
    (ProtectionMode.protected, True, {'roles': {'create'}}, True),
    # restricted - not authorized
    (ProtectionMode.public, True, None, False),
    (ProtectionMode.protected, True, None, False),
    (ProtectionMode.protected, True, {'read_access': True}, False)
))
def test_can_create_events(dummy_category, dummy_user, protection_mode, creation_restricted, acl, allowed):
    dummy_category.protection_mode = protection_mode
    dummy_category.event_creation_restricted = creation_restricted
    if acl:
        dummy_category.update_principal(dummy_user, **acl)
    assert dummy_category.can_create_events(dummy_user) == allowed


def test_can_create_events_no_user(dummy_category):
    assert not dummy_category.can_create_events(None)
