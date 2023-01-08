# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import os
from datetime import date, datetime
from pathlib import Path

import pytest
from flask import render_template

from indico.modules.rb.models.blocked_rooms import BlockedRoomState
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrenceState
from indico.modules.rb.models.reservations import RepeatFrequency, RepeatMapping, ReservationState
from indico.web.flask.templating import get_template_module


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def _assert_snapshot(snapshot, template_name, type,  suffix='', /, **context):
    __tracebackhide__ = True
    template = get_template_module(f'rb/emails/{type}/{template_name}', **context)
    snapshot.snapshot_dir = Path(__file__).parent.parent / f'templates/emails/{type}/tests'
    snapshot_name, snapshot_ext = os.path.splitext(template_name)
    snapshot.assert_match(template.get_body(), snapshot_name + suffix + snapshot_ext)


@pytest.mark.parametrize(('suffix', 'rooms'), (
    ('', 1),
    ('_rooms', 2),
))
def test_blocking_confirmation_email_plaintext(snapshot, dummy_room, dummy_user, create_blocking, suffix, rooms):
    room = [{'room': dummy_room} for n in range(rooms)]
    blocking = create_blocking(id=1, start_date=date(2022, 11, 11), end_date=date(2022, 11, 11))
    _assert_snapshot(snapshot, 'awaiting_confirmation_email_to_manager.txt', 'blockings', suffix,
                     blocking=blocking, blocked_rooms=room, owner=dummy_user)


@pytest.mark.parametrize(('suffix', 'state'), (
    ('_rejected', BlockedRoomState.rejected),
    ('_accepted', BlockedRoomState.accepted),
))
def test_blocking_state_email_plaintext(snapshot, create_blocking, dummy_room, suffix, state):
    blocking = create_blocking(id=2)
    _assert_snapshot(snapshot, 'state_email_to_user.txt', 'blockings', suffix,
                     blocking=blocking,
                     blocked_room={'room': dummy_room, 'state': state,
                                   'State': BlockedRoomState})


@pytest.mark.parametrize('snapshot_name', (
    'cancellation_email_to_manager.txt', 'cancellation_email_to_user.txt'
))
def test_reservation_cancellation_emails_plaintext(snapshot, snapshot_name, create_reservation):
    res = create_reservation(id=0, start_dt=datetime(2022, 11, 11, 13, 37), end_dt=datetime(2022, 11, 11, 14, 37))
    _assert_snapshot(snapshot, snapshot_name, 'reservations', reservation=res)


@pytest.mark.parametrize('snapshot_name', (
    'change_state_email_to_manager.txt', 'change_state_email_to_user.txt'
))
def test_reservation_change_state_emails_plaintext(snapshot, snapshot_name, create_reservation):
    res = create_reservation(id=0, start_dt=datetime(2022, 11, 11, 13, 37), end_dt=datetime(2022, 11, 11, 14, 37))
    _assert_snapshot(snapshot, snapshot_name, 'reservations', reservation=res)


@pytest.mark.parametrize(('snapshot_name', 'suffix', 'reason'), (
    ('confirmation_email_to_manager.txt', '_reason', 'Because I want to.'),
    ('confirmation_email_to_user.txt', '_reason', 'Because I want to.'),
    ('confirmation_email_to_manager.txt', '', ''),
    ('confirmation_email_to_user.txt', '', '')
))
def test_reservation_confirmation_emails_plaintext(snapshot, snapshot_name, create_reservation, suffix, reason):
    res = create_reservation(id=0, start_dt=datetime(2022, 11, 11, 13, 37), end_dt=datetime(2022, 11, 11, 14, 37))
    _assert_snapshot(snapshot, snapshot_name, 'reservations', suffix,
                     reservation=res, reason=reason)


@pytest.mark.parametrize(('snapshot_name', 'suffix', 'excluded_days', 'repeat'), (
    ('creation_email_to_manager.txt', '', None, RepeatFrequency.NEVER),
    ('creation_email_to_user.txt', '', None, RepeatFrequency.NEVER),
    ('creation_email_to_user.txt', '_repeat', None, RepeatFrequency.DAY),
    ('creation_email_to_user.txt', '_repeat_excluded_1', 1, RepeatFrequency.DAY),
    ('creation_email_to_user.txt', '_repeat_excluded_2', 2, RepeatFrequency.DAY),
    ('creation_email_to_manager.txt', '', None, RepeatFrequency.NEVER),
    ('creation_email_to_user.txt', '_pre', None, RepeatFrequency.NEVER),
    ('creation_email_to_user.txt', '_repeat_pre', None, RepeatFrequency.DAY),
    ('creation_email_to_user.txt', '_key', None, RepeatFrequency.NEVER),
    ('creation_email_to_user.txt', '_pre_key', None, RepeatFrequency.NEVER),
))
def test_reservation_creation_emails_plaintext(
    snapshot, snapshot_name, create_reservation, suffix, excluded_days, repeat
):
    res = create_reservation(id=1337, start_dt=datetime(2022, 11, 11, 13, 37), end_dt=datetime(2022, 11, 21, 14, 37),
                             repeat_frequency=repeat)
    if 'pre' in suffix:
        res.state = ReservationState.pending
    if excluded_days:
        for occ in res.occurrences[1:(excluded_days+1)]:
            occ.state = ReservationOccurrenceState.cancelled
    if 'key' in suffix:
        res.room.key_location = 'In a pocket dimension reachable via interpretative dance.'
    _assert_snapshot(snapshot, snapshot_name, 'reservations', suffix, reservation=res,
                     RepeatMapping=RepeatMapping, RepeatFrequency=RepeatFrequency)


@pytest.mark.parametrize('snapshot_name', (
    'modification_email_to_manager.txt', 'modification_email_to_user.txt'
))
def test_reservation_modification_emails_plaintext(snapshot, snapshot_name, create_reservation):
    res = create_reservation(id=0, start_dt=datetime(2022, 11, 11, 13, 37), end_dt=datetime(2022, 11, 11, 14, 37))
    _assert_snapshot(snapshot, snapshot_name, 'reservations', reservation=res)


@pytest.mark.parametrize('snapshot_name', (
    'occurrence_cancellation_email_to_manager.txt', 'occurrence_cancellation_email_to_user.txt',
    'occurrence_rejection_email_to_manager.txt', 'occurrence_rejection_email_to_user.txt'
))
def test_reservation_occurrence_emails_plaintext(snapshot, snapshot_name, create_reservation):
    res = create_reservation(id=0, start_dt=datetime(2022, 11, 11, 13, 37), end_dt=datetime(2022, 11, 12, 14, 37))
    occurrence = {'start_dt': datetime(2022, 11, 11, 13, 37), 'rejection_reason': 'A valid reason!'}
    _assert_snapshot(snapshot, snapshot_name, 'reservations', reservation=res, occurrence=occurrence)


@pytest.mark.parametrize('snapshot_name', (
    'rejection_email_to_manager.txt', 'rejection_email_to_user.txt'
))
def test_reservation_rejection_emails_plaintext(snapshot, snapshot_name, create_reservation):
    res = create_reservation(id=0, start_dt=datetime(2022, 11, 11, 13, 37), end_dt=datetime(2022, 11, 11, 14, 37))
    _assert_snapshot(snapshot, snapshot_name, 'reservations',
                     reservation=res, reason='Because I want to.')


@pytest.mark.parametrize('snapshot_name', (
    'reservation_info.txt', 'reservation_key_info.txt'
))
def test_reservation_emails_plaintext(snapshot, snapshot_name, create_reservation):
    res = create_reservation(id=0, start_dt=datetime(2022, 11, 11, 13, 37), end_dt=datetime(2022, 11, 11, 14, 37))
    res.room.key_location = 'In a pocket dimension reachable via interpretative dance.'
    template = render_template(f'rb/emails/reservations/{snapshot_name}', reservation=res)
    snapshot.snapshot_dir = Path(__file__).parent.parent / 'templates/emails/reservations/tests'
    snapshot.assert_match(template, snapshot_name)
