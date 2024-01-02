# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest
from werkzeug.datastructures import MultiDict

from indico.modules.auth import Identity
from indico.modules.groups.models.groups import LocalGroup
from indico.modules.rb import rb_settings
from indico.modules.users import User


@pytest.fixture
def create_user(db):
    """Return a callable which lets you create dummy users."""
    def _create_user(id_, first_name='Guinea', last_name='Pig', rb_admin=False, admin=False, email=None, groups=None):
        user = User.get(id_)
        if user:
            return user
        user = User()
        user.id = id_
        user.first_name = first_name
        user.last_name = last_name
        user.email = email or f'{id_}@example.test'
        user.is_admin = admin
        user.local_groups = {g.group for g in (groups or ())}
        db.session.add(user)
        db.session.flush()
        if rb_admin:
            rb_settings.acls.add_principal('admin_principals', user)
        db.session.flush()
        return user

    return _create_user


@pytest.fixture
def dummy_user(create_user):
    """Create a mocked user."""
    return create_user(1337)


@pytest.fixture
def create_group(db):
    """Return a callable which lets you create dummy groups."""
    def _create_group(id_, group_name=None):
        group = LocalGroup()
        group.id = id_
        group.name = group_name or f'dummy-{id_}'
        db.session.add(group)
        db.session.flush()
        return group.proxy

    return _create_group


@pytest.fixture
def dummy_group(create_group):
    """Create a mocked dummy group."""
    return create_group(1337)


@pytest.fixture
def create_identity(db):
    """Return a callable which lets you create dummy identities."""
    def _create_identity(user, provider, identifier, **kwargs):
        identity = Identity(user=user, provider=provider, identifier=identifier, **kwargs)
        db.session.flush()
        return identity

    return _create_identity


@pytest.fixture
def dummy_identity(dummy_user, create_identity):
    """Create a dummy identity."""
    data = MultiDict([('foo', 'bar'), ('foo', 'baz')])
    return create_identity(dummy_user, provider='ldap', identifier='guinea_pig', data=data)
