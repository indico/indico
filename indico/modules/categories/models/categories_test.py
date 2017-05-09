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
from sqlalchemy.orm import undefer

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.categories import Category


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


def test_effective_protection_mode(db):
    def _cat(id_, protection_mode=ProtectionMode.inheriting, children=None):
        return Category(id=id_, title='cat-{}'.format(id_), protection_mode=protection_mode, children=children or [])
    root = Category.get_root()
    root.protection_mode = ProtectionMode.protected
    root.children = [
        _cat(1),
        _cat(2, ProtectionMode.public, children=[
            _cat(3, children=[
                _cat(4, ProtectionMode.inheriting),
                _cat(5, ProtectionMode.public),
                _cat(6, ProtectionMode.protected),
            ]),
            _cat(7, ProtectionMode.protected, children=[
                _cat(8, ProtectionMode.inheriting),
                _cat(9, ProtectionMode.public),
                _cat(10, ProtectionMode.protected),
            ]),
            _cat(11)
        ])
    ]
    db.session.add(root)
    db.session.flush()
    data = {c.id: c.effective_protection_mode for c in Category.query.options(undefer('effective_protection_mode'))}
    assert data == {
        0: ProtectionMode.protected,
        1: ProtectionMode.protected,
        2: ProtectionMode.public,
        3: ProtectionMode.public,
        4: ProtectionMode.public,
        5: ProtectionMode.public,
        6: ProtectionMode.protected,
        7: ProtectionMode.protected,
        8: ProtectionMode.protected,
        9: ProtectionMode.public,
        10: ProtectionMode.protected,
        11: ProtectionMode.public
    }


@pytest.fixture
def category_family(create_category, db):
    grandpa = Category.get_root()
    dad = create_category(1, title='Dad', parent=grandpa)
    son = create_category(2, title='Son', parent=dad)
    sibling = create_category(3, title='Sibling', parent=dad)

    db.session.add(son)
    db.session.flush()

    return grandpa, dad, son, sibling


def test_nth_parent(category_family):
    grandpa, dad, son, sibling = category_family

    assert son.nth_parent(0) == son
    assert son.nth_parent(1) == dad
    assert son.nth_parent(2) == grandpa
    assert dad.nth_parent(0) == dad
    assert dad.nth_parent(1) == grandpa

    assert sibling.nth_parent(2) == grandpa
    assert sibling.nth_parent(0) != son.nth_parent(0)
    assert sibling.nth_parent(1) == son.nth_parent(1)
    assert sibling.nth_parent(2) == son.nth_parent(2)

    pytest.raises(IndexError, grandpa.nth_parent, 1)
    pytest.raises(IndexError, dad.nth_parent, 2)
    pytest.raises(IndexError, son.nth_parent, 3)
    pytest.raises(IndexError, grandpa.nth_parent, 100)


def test_is_descendant_of(category_family):
    grandpa, dad, son, sibling = category_family

    assert not dad.is_descendant_of(dad)
    assert not dad.is_descendant_of(son)
    assert son.is_descendant_of(dad)
    assert son.is_descendant_of(grandpa)
    assert dad.is_descendant_of(grandpa)


def test_visibility_horizon_default(category_family):
    grandpa, dad, son, sibling = category_family

    # default settings, no overriding
    assert son.own_visibility_horizon == grandpa
    assert dad.own_visibility_horizon == grandpa
    assert grandpa.own_visibility_horizon == grandpa
    assert son.real_visibility_horizon == grandpa
    assert dad.real_visibility_horizon == grandpa
    assert grandpa.real_visibility_horizon == grandpa


def test_visibility_horizon_limitation(category_family, create_category):
    grandpa, dad, son, sibling = category_family
    grandson = create_category(4, title='Grandson', parent=son)

    son.visibility = 1  # itself

    assert son.own_visibility_horizon == son.real_visibility_horizon
    assert son.own_visibility_horizon == son

    son.visibility = 2  # dad

    # 'son' and 'grandson' shouldn't be visible from above 'dad'
    assert son.real_visibility_horizon == dad
    assert grandson.real_visibility_horizon == dad

    # sibling should be visible from top, though
    assert sibling.real_visibility_horizon == grandpa

    dad.visibility = 1  # everything limited to 'dad'

    assert son.real_visibility_horizon == dad
    assert grandson.real_visibility_horizon == dad
    assert sibling.real_visibility_horizon == dad
