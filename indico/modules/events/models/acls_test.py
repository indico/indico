# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.roles import get_available_roles
from indico.modules.events import Event
from indico.modules.events.models.principals import EventPrincipal
from indico.testing.util import bool_matrix


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
def test_update_principal_signal(create_event, dummy_user):
    event = create_event()
    calls = []

    def _signal_fn(sender, **kwargs):
        assert not calls
        calls.append(kwargs)

    with signals.acl.entry_changed.connected_to(_signal_fn, sender=Event):
        # not in acl
        event.remove_principal(dummy_user)
        assert not calls
        # not added
        event.update_principal(dummy_user)
        assert not calls
        # adding new entry
        entry = event.update_principal(dummy_user, full_access=True, roles={'foo'})
        call = calls.pop()
        assert call['is_new']
        assert call['obj'] is event
        assert call['principal'] == dummy_user
        assert call['entry'] == entry
        assert call['old_data'] == {'read_access': False, 'full_access': False, 'roles': set()}
        assert not call['quiet']
        # updating entry
        event.update_principal(dummy_user, add_roles={'bar'})
        call = calls.pop()
        assert not call['is_new']
        assert call['obj'] is event
        assert call['principal'] == dummy_user
        assert call['entry'] == entry
        assert call['old_data'] == {'read_access': False, 'full_access': True, 'roles': {'foo'}}
        assert not call['quiet']
        # removing entry + quiet
        event.update_principal(dummy_user, full_access=False, roles=set(), quiet=True)
        call = calls.pop()
        assert not call['is_new']
        assert call['obj'] is event
        assert call['principal'] == dummy_user
        assert call['entry'] is None
        assert call['old_data'] == {'read_access': False, 'full_access': True, 'roles': {'foo', 'bar'}}
        assert call['quiet']


@pytest.mark.usefixtures('request_context')
def test_update_principal_resolve_email(create_event, create_user):
    event = create_event()
    user = create_user(123, email='user@example.com')
    # add email that belongs to a user
    entry = event.update_principal(EmailPrincipal('user@example.com'), full_access=True)
    assert entry.principal == user
    assert entry.type == PrincipalType.user
    # add email that has no user associated
    entry = event.update_principal(EmailPrincipal('unknown@example.com'), full_access=True)
    assert entry.principal == EmailPrincipal('unknown@example.com')
    assert entry.type == PrincipalType.email


@pytest.mark.usefixtures('request_context')
def test_convert_email_principals(db, create_event, create_user, dummy_user):
    event = create_event()
    user = create_user(123, email='user@example.com')
    principal = EmailPrincipal('unknown@example.com')
    other_entry = event.update_principal(dummy_user, full_access=True, roles={'foo', 'foobar'})
    entry = event.update_principal(principal, read_access=True, roles={'foo', 'bar'})
    other_entry_data = other_entry.current_data
    entry_data = entry.current_data
    # different emails for now -> nothing updated
    assert not EventPrincipal.replace_email_with_user(user, 'event')
    assert set(event.acl_entries) == {entry, other_entry}
    user.secondary_emails.add(principal.email)
    assert EventPrincipal.replace_email_with_user(user, 'event') == {event}
    assert set(event.acl_entries) == {entry, other_entry}
    assert all(x.type == PrincipalType.user for x in event.acl_entries)
    db.session.expire(other_entry)
    db.session.expire(entry)
    assert entry.current_data == entry_data
    assert other_entry.current_data == other_entry_data


@pytest.mark.usefixtures('request_context')
def test_convert_email_principals_merge(db, create_event, create_user):
    event = create_event()
    user = create_user(123, email='user@example.com')
    principal = EmailPrincipal('unknown@example.com')
    entry1 = event.update_principal(user, full_access=True, roles={'foo', 'foobar'})
    entry2 = event.update_principal(principal, read_access=True, roles={'foo', 'bar'})
    # different emails for now -> nothing updated
    assert not EventPrincipal.replace_email_with_user(user, 'event')
    assert set(event.acl_entries) == {entry1, entry2}
    user.secondary_emails.add(principal.email)
    assert EventPrincipal.replace_email_with_user(user, 'event') == {event}
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


def test_can_access_key_outside_context(create_event):
    event = create_event(protection_mode=ProtectionMode.protected, access_key='12345')
    assert not event.can_access(None)


def test_check_access_key(create_event):
    event = create_event(protection_mode=ProtectionMode.protected, access_key='12345')
    assert not event.check_access_key('foobar')
    assert event.check_access_key('12345')


@pytest.mark.usefixtures('request_context')
def test_can_access_key(create_event):
    event = create_event(protection_mode=ProtectionMode.protected, access_key='12345')
    assert not event.can_access(None)
    event.set_session_access_key('12345')
    assert event.can_access(None)
    event.set_session_access_key('foobar')
    assert not event.can_access(None)
    # make sure we never accept empty access keys
    event.access_key = ''
    event.set_session_access_key('')
    assert not event.can_access(None)


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

    with signals.acl.can_manage.connected_to(partial(_signal_fn, rv=signal_rv_1), sender=Event):
        with signals.acl.can_manage.connected_to(partial(_signal_fn, rv=signal_rv_2), sender=Event):
            assert event.can_manage(dummy_user) == allowed


@pytest.mark.parametrize(('signal_rv_1', 'signal_rv_2', 'allowed'), (
    (False, False, False),
    (False, True,  False),
    (True,  True,  True)
))
def test_can_access_signal_override(create_event, dummy_user, signal_rv_1, signal_rv_2, allowed):
    event = create_event()

    def _signal_fn(sender, obj, user, rv, **kwargs):
        assert obj is event
        assert user is dummy_user
        return rv

    with signals.acl.can_access.connected_to(partial(_signal_fn, rv=signal_rv_1), sender=Event):
        with signals.acl.can_access.connected_to(partial(_signal_fn, rv=signal_rv_2), sender=Event):
            assert event.can_access(dummy_user) == allowed


def test_can_access_signal_override_calls(create_event, dummy_user):
    event = create_event()

    def _signal_fn_noreturn(sender, authorized,  **kwargs):
        calls.append(authorized)

    def _signal_fn_early(sender, authorized,  **kwargs):
        calls.append(authorized)
        return True if authorized is None else None

    def _signal_fn_late(sender, authorized,  **kwargs):
        calls.append(authorized)
        return True if authorized is not None else None

    # early check - signal only invoked once since we return something
    calls = []
    with signals.acl.can_access.connected_to(_signal_fn_early, sender=Event):
        event.can_access(dummy_user)
    assert calls == [None]

    # signal invoked twice (nothing returned)
    calls = []
    with signals.acl.can_access.connected_to(_signal_fn_noreturn, sender=Event):
        event.can_access(dummy_user)
    assert calls == [None, True]

    # late check - signal invoked twice, once with the regular access state
    calls = []
    with signals.acl.can_access.connected_to(_signal_fn_late, sender=Event):
        event.can_access(dummy_user)
    assert calls == [None, True]

    # late check - signal invoked twice, once with the regular access state
    calls = []
    event.protection_mode = ProtectionMode.protected
    with signals.acl.can_access.connected_to(_signal_fn_late, sender=Event):
        event.can_access(dummy_user)
    assert calls == [None, False]


@pytest.mark.parametrize(('is_admin', 'allow_admin', 'not_explicit', 'expected'), bool_matrix('...', expect=all))
def test_can_manage_admin(create_event, create_user, is_admin, allow_admin, not_explicit, expected):
    event = create_event()
    user = create_user(123, admin=is_admin)
    assert event.can_manage(user, allow_admin=allow_admin, explicit_role=not not_explicit) == expected


def test_can_manage_guest(create_event, dummy_category):
    event = create_event()
    # we grant explicit management access on the parent to ensure that
    # we don't even check there but bail out early
    event.category = dummy_category
    event.category.can_manage = MagicMock(return_value=True)
    assert not event.can_manage(None)


@pytest.mark.parametrize('can_manage_parent', (True, False))
def test_can_manage_parent(create_event, dummy_category, dummy_user, can_manage_parent):
    event = create_event()
    event.category = dummy_category
    event.category.can_manage = MagicMock(return_value=can_manage_parent)
    assert event.can_manage(dummy_user) == can_manage_parent
    event.category.can_manage.assert_called_once_with(dummy_user, allow_admin=True)


def test_can_manage_parent_invalid(create_event, dummy_user):
    event = create_event()
    event.__dict__['category'] = MagicMock(spec=[])
    with pytest.raises(TypeError):
        event.can_manage(dummy_user)


def test_can_manage_roles_invalid(create_event, dummy_user):
    event = create_event()
    with pytest.raises(ValueError):
        event.can_manage(dummy_user, 'invalid')


def test_merge_privs():
    p = EventPrincipal(read_access=True, roles={'foo', 'bar'})
    p.merge_privs(EventPrincipal(roles={'bar', 'foobar'}, full_access=True))
    assert p.read_access
    assert p.full_access
    assert set(p.roles) == {'foo', 'bar', 'foobar'}


def test_has_management_role_full_access():
    p = EventPrincipal(full_access=True, roles=[])
    assert p.has_management_role()
    assert p.has_management_role('foo')
    assert p.has_management_role('ANY')


@pytest.mark.usefixtures('request_context')
def test_has_management_role_full_access_db(create_event, dummy_user, create_user):
    event = create_event()
    event.update_principal(create_user(123), roles={'bar'})
    entry = event.update_principal(dummy_user, full_access=True)

    def _find(*args):
        return EventPrincipal.find(EventPrincipal.event == event, EventPrincipal.has_management_role(*args))

    assert _find().one() == entry
    assert _find('foo').one() == entry
    assert _find('ANY').count() == 2


def test_has_management_role_no_access():
    p = EventPrincipal(read_access=True, roles=[])
    assert not p.has_management_role()
    assert not p.has_management_role('foo')
    assert not p.has_management_role('ANY')


@pytest.mark.usefixtures('request_context')
def test_has_management_role_no_access_db(create_event, dummy_user):
    event = create_event()
    event.update_principal(dummy_user, read_access=True)

    def _find(*args):
        return EventPrincipal.find(EventPrincipal.event == event, EventPrincipal.has_management_role(*args))

    assert not _find().count()
    assert not _find('foo').count()
    assert not _find('ANY').count()


@pytest.mark.parametrize('explicit', (True, False))
def test_has_management_role_explicit(explicit):
    p = EventPrincipal(full_access=True, roles=['foo'])
    assert p.has_management_role('foo', explicit=explicit)
    assert p.has_management_role('ANY', explicit=explicit)
    assert p.has_management_role('bar', explicit=explicit) == (not explicit)
    assert EventPrincipal(full_access=True, roles=[]).has_management_role('ANY', explicit=explicit) == (not explicit)


@pytest.mark.parametrize('explicit', (True, False))
@pytest.mark.usefixtures('request_context')
def test_has_management_role_explicit_db(create_event, dummy_user, create_user, explicit):
    event = create_event()
    event.update_principal(create_user(123), full_access=True)
    event.update_principal(dummy_user, full_access=True, roles={'foo'})

    def _find(role):
        return EventPrincipal.find(EventPrincipal.event == event,
                                   EventPrincipal.has_management_role(role, explicit=explicit))

    assert _find('foo').count() == (1 if explicit else 2)
    assert _find('bar').count() == (0 if explicit else 2)
    assert _find('ANY').count() == (1 if explicit else 2)


def test_has_management_role_explicit_fail():
    p = EventPrincipal(roles=['foo'])
    # no role specified
    with pytest.raises(ValueError):
        p.has_management_role(explicit=True)
    with pytest.raises(ValueError):
        EventPrincipal.has_management_role(explicit=True)


def test_has_management_role():
    p = EventPrincipal(roles=['foo'])
    assert p.has_management_role('ANY')
    assert p.has_management_role('foo')
    assert not p.has_management_role('bar')


@pytest.mark.usefixtures('request_context')
def test_has_management_role_db(create_event, create_user, dummy_user):
    event = create_event()
    event.update_principal(create_user(123), roles={'bar'})
    entry = event.update_principal(dummy_user, roles={'foo'})

    def _find(*args):
        return EventPrincipal.find(EventPrincipal.event == event, EventPrincipal.has_management_role(*args))

    assert not _find().count()
    assert _find('foo').one() == entry
    assert _find('ANY').count() == 2
