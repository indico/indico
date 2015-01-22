# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from indico.modules.rb.models.blocking_principals import BlockingPrincipal


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_entity_user(dummy_user):
    principal = BlockingPrincipal(entity_type='Avatar', entity_id=dummy_user.id)
    assert principal.entity == dummy_user
    assert principal.entity_name == 'User'


def test_entity_group(dummy_group):
    principal = BlockingPrincipal(entity_type='Group', entity_id=dummy_group.id)
    assert principal.entity == dummy_group
    assert principal.entity_name == 'Group'
