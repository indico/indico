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

from functools import partial

import pytest
from mock import MagicMock

from indico.core import signals
from indico.core.db.sqlalchemy.principals import EmailPrincipal, PrincipalType
from indico.core.roles import get_available_roles
from indico.modules.events import Event
from indico.modules.events.models.principals import EventPrincipal
from indico.testing.util import bool_matrix, extract_emails


@pytest.fixture(autouse=True)
def _mock_available_roles(mocker):
    # The code we are testing only cares about the keys so we don't
    # need to actually create roles for now.
    roles = dict(get_available_roles(Event), foo=None, bar=None, foobar=None)
    mocker.patch('indico.core.db.sqlalchemy.protection.get_available_roles', return_value=roles)
    mocker.patch('indico.core.db.sqlalchemy.principals.get_available_roles', return_value=roles)


@pytest.mark.usefixtures('request_context')
def test_remove_principal(db, create_event, create_user, dummy_user, dummy_group):
    event = create_event()
    event.update_principal(dummy_user, full_access=True)
    event.update_principal(dummy_group, full_access=True)
    db.session.flush()
    assert {p.principal for p in event.acl_entries} == {dummy_user, dummy_group}
    event.remove_principal(dummy_group)
    assert {p.principal for p in event.acl_entries} == {dummy_user}
    # removing some other user who's not in the acl doesn't do anything
    event.remove_principal(create_user(123))
    assert {p.principal for p in event.acl_entries} == {dummy_user}


@pytest.mark.usefixtures('request_context')
def test_update_principal(create_event, dummy_user):
    event = create_event()
    assert not event.acl_entries
    # not changing anything -> shouldn't be added to acl
    entry = event.update_principal(dummy_user)
    assert entry is None
    assert not event.acl_entries
    # adding user with read access -> new acl entry since the user isn't in there yet
    entry = initial_entry = event.update_principal(dummy_user, read_access=True)
    assert not entry.roles
    assert not entry.full_access
    assert entry.read_access
    assert event.acl_entries == {entry}
    # adding a role
    entry = event.update_principal(dummy_user, add_roles={'foo'})
    assert entry is initial_entry
    assert set(entry.roles) == {'foo'}
    assert not entry.full_access
    assert entry.read_access
    # adding yet another role
    entry = event.update_principal(dummy_user, add_roles={'foo', 'bar'})
    assert entry is initial_entry
    assert set(entry.roles) == {'foo', 'bar'}
    assert not entry.full_access
    assert entry.read_access
    # replacing the roles
    entry = event.update_principal(dummy_user, roles={'bar', 'foobar'})
    assert entry is initial_entry
    assert set(entry.roles) == {'bar', 'foobar'}
    assert not entry.full_access
    assert entry.read_access
    # removing explicit read access but adding full manager access instead
    entry = event.update_principal(dummy_user, read_access=False, full_access=True)
    assert entry is initial_entry
    assert set(entry.roles) == {'bar', 'foobar'}
    assert entry.full_access
    assert not entry.read_access
    # removing a role
    entry = event.update_principal(dummy_user, del_roles={'foobar', 'foo'})
    assert entry is initial_entry
    assert set(entry.roles) == {'bar'}
    assert entry.full_access
    assert not entry.read_access
    # removing the remaining access
    entry = event.update_principal(dummy_user, del_roles={'bar'}, full_access=False)
    assert entry is None
    assert not event.acl_entries


@pytest.mark.usefixtures('request_context')
def test_update_principal_resolve_email(create_event, create_user, smtp):
    event = create_event()
    user = create_user(123, email='user@example.com')
    # add email that belongs to a user
    entry = event.update_principal(EmailPrincipal('user@example.com'), full_access=True)
    assert entry.principal == user
    assert entry.type == PrincipalType.user
    extract_emails(smtp, required=False, count=0)
    # add email that has no user associated
    entry = event.update_principal(EmailPrincipal('unknown@example.com'), full_access=True)
    assert entry.principal == EmailPrincipal('unknown@example.com')
    assert entry.type == PrincipalType.email
    extract_emails(smtp, required=True, count=1)


@pytest.mark.usefixtures('request_context')
def test_update_principal_email(create_event, smtp):
    event = create_event()
    principal = EmailPrincipal('unknown@example.com')
    event.update_principal(principal, roles={'submit'})
    email = extract_emails(smtp, required=True, one=True, to=principal.email)
    assert email['Subject'] == '[Indico] Please register'
    # adding more privs to the user should not send another email
    event.update_principal(principal, full_access=True)
    extract_emails(smtp, required=False, count=0)


@pytest.mark.usefixtures('request_context')
def test_convert_email_principals(db, create_event, create_user):
    event = create_event()
    user = create_user(123, email='user@example.com')
    principal = EmailPrincipal('unknown@example.com')
    entry1 = event.update_principal(user, full_access=True, roles={'foo', 'foobar'})
    entry2 = event.update_principal(principal, read_access=True, roles={'foo', 'bar'})
    # different emails for now -> nothing updated
    assert not EventPrincipal.replace_email_with_user(user, 'event_new')
    assert set(event.acl_entries) == {entry1, entry2}
    user.secondary_emails.add(principal.email)
    db.session.expire(user, ['_all_emails'])
    assert EventPrincipal.replace_email_with_user(user, 'event_new') == {event}
    assert len(event.acl_entries) == 1
    entry = list(event.acl_entries)[0]
    assert entry.full_access
    assert entry.read_access
    assert set(entry.roles) == {'foo', 'bar', 'foobar'}


def test_update_principal_errors(create_event, dummy_user):
    event = create_event()
    with pytest.raises(ValueError):
        event.update_principal(dummy_user, roles={'foo'}, add_roles={'bar'})
    with pytest.raises(ValueError):
        event.update_principal(dummy_user, roles={'foo'}, del_roles={'bar'})
    with pytest.raises(ValueError):
        event.update_principal(dummy_user, roles={'invalid'})


@pytest.mark.parametrize(('allow_key', 'has_key', 'expected'), bool_matrix('..', expect=all))
def test_can_manage_key(create_event, dummy_user, allow_key, has_key, expected):
    event = create_event()
    event.as_legacy.canKeyModify = lambda: has_key
    assert event.can_manage(dummy_user, allow_key=allow_key) == expected


@pytest.mark.usefixtures('request_context')
def test_can_manage_roles(create_event, dummy_user):
    event = create_event()
    assert not event.can_manage(dummy_user, 'ANY')
    event.update_principal(dummy_user, roles={'foo'})
    assert not event.can_manage(dummy_user)
    assert not event.can_manage(dummy_user, 'bar')
    assert event.can_manage(dummy_user, 'foo')
    assert event.can_manage(dummy_user, 'ANY')


@pytest.mark.parametrize(('signal_rv_1', 'signal_rv_2', 'allowed'), (
    (False, False, False),
    (False, True,  False),
    (True,  True,  True)
))
def test_can_manage_signal_override(create_event, dummy_user, signal_rv_1, signal_rv_2, allowed):
    event = create_event()

    def _signal_fn(sender, obj, user, rv, **kwargs):
        assert obj is event
        assert user is dummy_user
        return rv

    with signals.acl.can_manage.connected_to(partial(_signal_fn, rv=signal_rv_1)):
        with signals.acl.can_manage.connected_to(partial(_signal_fn, rv=signal_rv_2)):
            assert event.can_manage(dummy_user) == allowed


@pytest.mark.parametrize(('is_admin', 'allow_admin', 'not_explicit', 'expected'), bool_matrix('...', expect=all))
def test_can_manage_admin(create_event, create_user, is_admin, allow_admin, not_explicit, expected):
    event = create_event()
    user = create_user(123, admin=is_admin)
    assert event.can_manage(user, allow_admin=allow_admin, explicit_role=not not_explicit) == expected


def test_can_manage_guest(create_event):
    event = create_event()
    # we grant explicit management access on the parent to ensure that
    # we don't even check there but bail out early
    event.as_legacy.category = MagicMock(spec=['can_manage'])
    event.as_legacy.category.can_manage.return_value = True
    assert not event.can_manage(None)


@pytest.mark.parametrize('can_manage_parent', (True, False))
def test_can_manage_parent(create_event, dummy_user, can_manage_parent):
    event = create_event()
    event.as_legacy.category = MagicMock(spec=['can_manage'])
    event.as_legacy.category.can_manage.return_value = can_manage_parent
    assert event.can_manage(dummy_user) == can_manage_parent
    event.as_legacy.category.can_manage.assert_called_once_with(dummy_user, allow_admin=True)


@pytest.mark.parametrize('can_manage_parent', (True, False))
def test_can_manage_parent_legacy(create_event, dummy_user, can_manage_parent):
    event = create_event()
    event.as_legacy.category = MagicMock(spec=['canUserModify'])
    event.as_legacy.category.canUserModify.return_value = can_manage_parent
    assert event.can_manage(dummy_user) == can_manage_parent
    event.as_legacy.category.canUserModify.assert_called_once_with(dummy_user.as_avatar)


def test_can_manage_parent_invalid(create_event, dummy_user):
    event = create_event()
    event.as_legacy.category = MagicMock(spec=[])
    with pytest.raises(TypeError):
        event.can_manage(dummy_user)


def test_can_manage_roles_invalid(create_event, dummy_user):
    event = create_event()
    with pytest.raises(ValueError):
        event.can_manage(dummy_user, 'invalid')
