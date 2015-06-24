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

import pytest
from sqlalchemy import inspect

from indico.modules.groups.models.groups import LocalGroup
from indico.modules.rb import settings as rb_settings
from indico.modules.users import User


@pytest.yield_fixture
def create_user(db):
    """Returns a callable which lets you create dummy users"""
    _users = set()

    def _create_user(id_, first_name=u'Guinea', last_name=u'Pig', rb_admin=False, admin=False, email=None, groups=None,
                     legacy=False):
        user = User.get(id_)
        if user:
            return user.as_avatar if legacy else user
        user = User()
        user.id = id_
        user.first_name = first_name
        user.last_name = last_name
        user.email = email or u'{}@example.com'.format(id_)
        user.is_admin = admin
        user.local_groups = {g.group for g in (groups or ())}
        db.session.add(user)
        db.session.flush()
        if rb_admin:
            rb_settings.acls.add_principal('admin_principals', user)
        db.session.flush()
        _users.add(user)
        return user.as_avatar if legacy else user

    yield _create_user

    for user in _users:
        if inspect(user).persistent:  # avoid error if session was rolled back
            db.session.delete(user)


@pytest.fixture
def dummy_user(create_user):
    """Creates a mocked user"""
    return create_user(1337, legacy=False)


@pytest.fixture
def dummy_avatar(dummy_user):
    """Creates a mocked dummy legacy avatar"""
    return dummy_user.as_avatar


@pytest.yield_fixture
def create_group(db):
    """Returns a callable which lets you create dummy groups"""
    _groups = set()

    def _create_group(id_):
        group = LocalGroup()
        group.id = id_
        group.name = u'dummy-{}'.format(id_)
        db.session.add(group)
        db.session.flush()
        _groups.add(group)
        return group.proxy

    yield _create_group

    for group in _groups:
        if inspect(group).persistent:  # avoid error if session was rolled back
            db.session.delete(group)


@pytest.fixture
def dummy_group(create_group):
    """Creates a mocked dummy group"""
    return create_group(1337)
