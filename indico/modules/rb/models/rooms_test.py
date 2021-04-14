# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date, datetime, time, timedelta

import pytest

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.core.errors import IndicoError
from indico.modules.rb import rb_settings
from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.photos import Photo
from indico.modules.rb.models.reservations import RepeatFrequency, ReservationState
from indico.modules.rb.models.room_bookable_hours import BookableHours
from indico.modules.rb.models.rooms import Room
from indico.modules.users import User
from indico.testing.util import bool_matrix
from indico.util.date_time import get_day_end, get_day_start


pytest_plugins = 'indico.modules.rb.testing.fixtures'
_notset = object()


@pytest.mark.parametrize('need_confirmation', (True, False))
def test_is_auto_confirm(create_room, need_confirmation):
    room = create_room(reservations_need_confirmation=need_confirmation)
    assert room.is_auto_confirm != need_confirmation
    assert Room.query.filter_by(is_auto_confirm=need_confirmation).first() is None
    assert Room.query.filter_by(is_auto_confirm=not need_confirmation).first() == room


def test_has_photo(db, dummy_room):
    assert not dummy_room.has_photo
    dummy_room.photo = Photo()
    db.session.flush()
    assert dummy_room.has_photo


@pytest.mark.parametrize(('building', 'floor', 'number', 'verbose_name', 'expected_name'), (
    ('1', '2', '3', None,      '1/2-3'),
    ('1', '2', 'X', None,      '1/2-X'),
    ('1', 'X', '3', None,      '1/X-3'),
    ('X', '2', '3', None,      'X/2-3'),
    ('1', '2', '3', 'Test',   '1/2-3 - Test'),
    ('1', '2', '3', 'm\xf6p', '1/2-3 - m\xf6p')
))
def test_full_name(create_room, building, floor, number, verbose_name, expected_name):
    room = create_room(building=building, floor=floor, number=number, verbose_name=verbose_name)
    assert room.full_name == expected_name


@pytest.mark.parametrize(('name',), (
    (None,),
    ('1/2-3',),
    ('Test',)
))
def test_name_stays_same(create_room, name):
    room = create_room(verbose_name=name)
    assert room.name == '1/2-3'


@pytest.mark.parametrize(('protection_mode', 'expected'), (
    (ProtectionMode.protected, False),
    (ProtectionMode.public, True),
))
def test_is_public(dummy_room, protection_mode, expected):
    dummy_room.protection_mode = protection_mode
    assert dummy_room.is_public == expected


def test_location_name(dummy_room, dummy_location):
    assert dummy_room.location_name == dummy_location.name


def test_owner(dummy_room, dummy_user):
    assert dummy_room.owner == dummy_user


def test_owner_after_change(dummy_room, dummy_user):
    dummy_room.owner = dummy_user
    assert dummy_room.owner == dummy_user


@pytest.mark.parametrize(('name', 'expected'), (
    ('foo', True),
    ('bar', True),
    ('xxx', False),  # existent
    ('yyy', False),  # not existent
))
def test_has_equipment(create_equipment_type, dummy_room, name, expected):
    dummy_room.available_equipment.append(create_equipment_type('foo'))
    dummy_room.available_equipment.append(create_equipment_type('bar'))
    create_equipment_type('xxx')
    assert dummy_room.has_equipment(name) == expected


def test_get_attribute_by_name(create_room_attribute, dummy_room):
    attr = create_room_attribute('foo')
    assert dummy_room.get_attribute_by_name('foo') is None
    dummy_room.set_attribute_value('foo', 'bar')
    assert dummy_room.get_attribute_by_name('foo').attribute == attr


def test_has_attribute(create_room_attribute, dummy_room):
    create_room_attribute('foo')
    assert not dummy_room.has_attribute('foo')
    dummy_room.set_attribute_value('foo', 'bar')
    assert dummy_room.has_attribute('foo')


@pytest.mark.parametrize(('value', 'expected'), (
    ('',        _notset),
    (None,       _notset),
    (0,          _notset),
    ([],         _notset),
    ('foo',     'foo'),
    (123,        123),
    (True,       True),
    (['a', 'b'], ['a', 'b']),
))
def test_get_attribute_value(create_room_attribute, dummy_room, value, expected):
    assert dummy_room.get_attribute_value('foo', _notset) is _notset
    create_room_attribute('foo')
    assert dummy_room.get_attribute_value('foo', _notset) is _notset
    dummy_room.set_attribute_value('foo', value)
    assert dummy_room.get_attribute_value('foo', _notset) == expected


def test_set_attribute_value(create_room_attribute, dummy_room):
    # setting an attribute that doesn't exist fails
    with pytest.raises(ValueError):
        dummy_room.set_attribute_value('foo', 'something')
    create_room_attribute('foo')
    # the value can be cleared even if it is not set
    dummy_room.set_attribute_value('foo', None)
    assert dummy_room.get_attribute_value('foo', _notset) is _notset
    # set it to some value
    dummy_room.set_attribute_value('foo', 'test')
    assert dummy_room.get_attribute_value('foo') == 'test'
    # set to some other value while we have an existing association entry
    dummy_room.set_attribute_value('foo', 'something')
    assert dummy_room.get_attribute_value('foo') == 'something'
    # clear it
    dummy_room.set_attribute_value('foo', None)
    assert dummy_room.get_attribute_value('foo', _notset) is _notset


def test_find_with_attribute(dummy_room, create_room, create_room_attribute):
    assert Room.query.all() == [dummy_room]  # one room without the attribute
    assert not Room.find_with_attribute('foo')
    create_room_attribute('foo')
    assert not Room.find_with_attribute('foo')
    expected = set()
    for room in [create_room(), create_room()]:
        value = f'bar-{room.id}'
        room.set_attribute_value('foo', value)
        expected.add((room, value))
    assert set(Room.find_with_attribute('foo')) == expected


def test_get_with_data_errors():
    with pytest.raises(ValueError):
        Room.get_with_data(foo='bar')


@pytest.mark.parametrize('only_active', (True, False))
def test_get_with_data(db, create_room, create_equipment_type, only_active):
    eq = create_equipment_type('eq')

    rooms = {
        'inactive': {'room': create_room(is_deleted=True), 'equipment': []},
        'no_eq': {'room': create_room(), 'equipment': []},
        'all_eq': {'room': create_room(), 'equipment': [eq]}
    }
    room_types = {room_data['room']: type_ for type_, room_data in rooms.items()}
    for room in rooms.values():
        room['room'].available_equipment = room['equipment']
    db.session.flush()
    results = list(Room.get_with_data(only_active=only_active))
    assert len(results) == len(rooms) - only_active
    for row in results:
        room = row.pop('room')
        room_type = room_types[room]
        if room_type == 'inactive':
            assert not only_active


@pytest.mark.parametrize(
    ('has_booking', 'has_blocking',
     'has_pre_booking', 'include_pre_bookings',
     'has_pending_blocking', 'include_pending_blockings',
     'filtered'),
    set(bool_matrix('00.0.0', expect=False) +                                # nothing confirmed/pending
        bool_matrix('000.0.', expect=False) +                                # nothing pending included
        bool_matrix('1.....', expect=True) +                                 # confirmed booking
        bool_matrix('.1....', expect=True) +                                 # active blocking
        bool_matrix('00....', expect=lambda x: all(x[2:4]) or all(x[4:6])))  # included pending booking/blocking
)
def test_filter_available(dummy_room, create_reservation, create_blocking,
                          has_booking, has_blocking,
                          has_pre_booking, include_pre_bookings,
                          has_pending_blocking, include_pending_blockings, filtered):
    if has_booking:
        create_reservation(start_dt=datetime.combine(date.today(), time(8)),
                           end_dt=datetime.combine(date.today(), time(10)))
    if has_pre_booking:
        create_reservation(start_dt=datetime.combine(date.today(), time(10)),
                           end_dt=datetime.combine(date.today(), time(12)),
                           state=ReservationState.pending)
    if has_blocking:
        create_blocking(state=BlockedRoom.State.accepted)
    if has_pending_blocking:
        create_blocking(state=BlockedRoom.State.pending)
    availabilty_filter = Room.filter_available(get_day_start(date.today()), get_day_end(date.today()),
                                               (RepeatFrequency.NEVER, 0), include_blockings=True,
                                               include_pre_bookings=include_pre_bookings,
                                               include_pending_blockings=include_pending_blockings)
    assert set(Room.query.filter(availabilty_filter)) == (set() if filtered else {dummy_room})


@pytest.mark.parametrize(('is_admin', 'is_owner', 'max_advance_days', 'days_delta', 'success'), (
    (True,  False, 10,   15, True),
    (False, True,  10,   15, True),
    (False, False, None, 15, True),
    (False, False, 0,    15, True),
    (False, False, 10,   -5, True),
    (False, False, 10,   10, False),
    (False, False, 10,   15, False)
))
def test_check_advance_days(create_user, dummy_room, is_admin, is_owner, max_advance_days, days_delta, success):
    user = create_user(123, rb_admin=is_admin)
    dummy_room.max_advance_days = max_advance_days
    end_date = date.today() + timedelta(days=days_delta)
    if is_owner:
        dummy_room.update_principal(user, full_access=True)
    if success:
        assert dummy_room.check_advance_days(end_date, user, quiet=True)
        assert dummy_room.check_advance_days(end_date, user)
    else:
        assert not dummy_room.check_advance_days(end_date, user, quiet=True)
        with pytest.raises(IndicoError):
            dummy_room.check_advance_days(end_date, user)


def test_check_advance_days_no_user(dummy_room):
    dummy_room.max_advance_days = 10
    end_date = date.today() + timedelta(days=15)
    assert not dummy_room.check_advance_days(end_date, quiet=True)


@pytest.mark.parametrize(('is_admin', 'is_owner', 'fits', 'success'), bool_matrix('...', expect=any))
def test_check_bookable_hours(db, dummy_room, create_user, is_admin, is_owner, fits, success):
    user = create_user(123, rb_admin=is_admin)
    if is_owner:
        dummy_room.update_principal(user, full_access=True)
    dummy_room.bookable_hours = [BookableHours(start_time=time(12), end_time=time(14))]
    db.session.flush()
    booking_hours = (time(12), time(13)) if fits else (time(8), time(9))
    if success:
        assert dummy_room.check_bookable_hours(booking_hours[0], booking_hours[1], user, quiet=True)
        assert dummy_room.check_bookable_hours(booking_hours[0], booking_hours[1], user)
    else:
        assert not dummy_room.check_bookable_hours(booking_hours[0], booking_hours[1], user, quiet=True)
        with pytest.raises(IndicoError):
            dummy_room.check_bookable_hours(booking_hours[0], booking_hours[1], user)


def test_check_bookable_hours_hours(dummy_room):
    assert dummy_room.check_bookable_hours(time(8), time(9), quiet=True)


def test_check_bookable_hours_no_user(db, dummy_room):
    dummy_room.bookable_hours = [BookableHours(start_time=time(12), end_time=time(14))]
    db.session.flush()
    assert not dummy_room.check_bookable_hours(time(8), time(9), quiet=True)


@pytest.mark.parametrize('reservations_need_confirmation', (True, False))
@pytest.mark.parametrize('is_owner', (True, False))
@pytest.mark.parametrize('is_reservable', (True, False))
def test_permissions_manager_owner(dummy_room, create_user, reservations_need_confirmation, is_owner, is_reservable):
    user = create_user(123)
    dummy_room.protection_mode = ProtectionMode.public
    dummy_room.reservations_need_confirmation = reservations_need_confirmation
    dummy_room.is_reservable = is_reservable
    if is_owner:
        dummy_room.owner = user
    else:
        dummy_room.update_principal(user, full_access=True)
    assert dummy_room.can_book(user) == is_reservable
    assert dummy_room.can_prebook(user) == (reservations_need_confirmation and is_reservable)
    assert dummy_room.can_override(user)
    assert dummy_room.can_moderate(user)


def test_permissions_manager_explicit_prebook(dummy_room, create_user):
    user = create_user(123)
    dummy_room.protection_mode = ProtectionMode.public
    dummy_room.update_principal(user, full_access=True, permissions={'prebook'})
    assert dummy_room.can_prebook(user)


@pytest.mark.parametrize('reservations_need_confirmation', (True, False))
def test_permissions_public_room(dummy_room, create_user, reservations_need_confirmation):
    user = create_user(123)
    dummy_room.protection_mode = ProtectionMode.public
    dummy_room.reservations_need_confirmation = reservations_need_confirmation
    assert dummy_room.can_book(user) == (not reservations_need_confirmation)
    assert dummy_room.can_prebook(user) == reservations_need_confirmation
    assert not dummy_room.can_override(user)
    assert not dummy_room.can_moderate(user)


def test_permissions_protected_room(dummy_room, create_user):
    user = create_user(123)
    dummy_room.protection_mode = ProtectionMode.protected
    assert not dummy_room.can_book(user)
    assert not dummy_room.can_prebook(user)
    assert not dummy_room.can_override(user)
    assert not dummy_room.can_moderate(user)


@pytest.mark.parametrize('reservations_need_confirmation', (True, False))
def test_permissions_protected_room_admin(dummy_room, create_user, reservations_need_confirmation):
    user = create_user(123)
    rb_settings.acls.add_principal('admin_principals', user)
    dummy_room.protection_mode = ProtectionMode.protected
    dummy_room.reservations_need_confirmation = reservations_need_confirmation
    assert dummy_room.can_book(user)
    assert dummy_room.can_prebook(user) == reservations_need_confirmation
    assert dummy_room.can_override(user)
    assert dummy_room.can_moderate(user)


@pytest.mark.parametrize('permission', ('book', 'prebook', 'override', 'moderate'))
def test_permissions_protected_room_acl(dummy_room, create_user, permission):
    user = create_user(123)
    dummy_room.protection_mode = ProtectionMode.protected
    dummy_room.update_principal(user, permissions={permission})
    for p in ('book', 'prebook', 'override', 'moderate'):
        granted = p == permission
        assert getattr(dummy_room, 'can_' + p)(user) == granted


def test_permissions_no_user(dummy_room):
    assert not dummy_room.can_book(None)
    assert not dummy_room.can_prebook(None)
    assert not dummy_room.can_override(None)
    assert not dummy_room.can_moderate(None)
    assert not dummy_room.can_edit(None)
    assert not dummy_room.can_delete(None)


@pytest.mark.parametrize('is_admin', (True, False))
def test_admin_permissions(dummy_room, create_user, is_admin):
    user = create_user(123)
    if is_admin:
        rb_settings.acls.add_principal('admin_principals', user)
    assert dummy_room.can_edit(user) == is_admin
    assert dummy_room.can_delete(user) == is_admin


@pytest.mark.parametrize('acl_perm', (None, 'book', 'prebook', 'override', 'moderate', '*'))
@pytest.mark.parametrize('protection_mode', (ProtectionMode.public, ProtectionMode.protected))
@pytest.mark.parametrize('reservations_need_confirmation', (True, False))
@pytest.mark.parametrize('is_reservable', (True, False))
@pytest.mark.parametrize('is_owner', (True, False))
@pytest.mark.parametrize('is_admin', (True, False))
@pytest.mark.parametrize('allow_admin', (True, False))
@pytest.mark.parametrize('bulk_possible', (True, False))
def test_get_permissions_for_user(dummy_room, create_user, monkeypatch, bulk_possible, allow_admin, is_admin, is_owner,
                                  is_reservable, reservations_need_confirmation, protection_mode, acl_perm):
    monkeypatch.setattr(User, 'can_get_all_multipass_groups', bulk_possible)
    user = create_user(123)
    if is_owner:
        dummy_room.owner = user
    if is_admin:
        rb_settings.acls.add_principal('admin_principals', user)
    dummy_room.protection_mode = protection_mode
    dummy_room.is_reservable = is_reservable
    dummy_room.reservations_need_confirmation = reservations_need_confirmation
    if acl_perm == '*':
        dummy_room.update_principal(user, full_access=True)
    elif acl_perm:
        dummy_room.update_principal(user, permissions={acl_perm})
    perms = Room.get_permissions_for_user(user, allow_admin=allow_admin)
    assert perms[dummy_room.id] == {
        'book': dummy_room.can_book(user, allow_admin=allow_admin),
        'prebook': dummy_room.can_prebook(user, allow_admin=allow_admin),
        'override': dummy_room.can_override(user, allow_admin=allow_admin),
        'moderate': dummy_room.can_moderate(user, allow_admin=allow_admin),
        'manage': dummy_room.can_manage(user, allow_admin=allow_admin),
    }
