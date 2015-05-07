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
    user = dummy_user.user
    assert BlockingPrincipal(principal=user).principal == user


def test_entity_group(dummy_group):
    assert BlockingPrincipal(principal=dummy_group).principal == dummy_group
