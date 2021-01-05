# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from datetime import date, datetime, time, timedelta

import pytest

from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.reservations import RepeatFrequency
from indico.testing.util import bool_matrix, extract_emails


pytest_plugins = 'indico.modules.rb.testing.fixtures'


@pytest.mark.parametrize('state', BlockedRoom.State)
def test_state_name(state):
    assert BlockedRoom(state=state).state_name == state.title


@pytest.mark.parametrize(('with_user', 'with_reason'), bool_matrix('..'))
def test_reject(dummy_user, dummy_blocking, smtp, with_user, with_reason):
    br = dummy_blocking.blocked_rooms[0]
    assert br.state == BlockedRoom.State.pending
    kwargs = {}
    if with_user:
        kwargs['user'] = dummy_user
    if with_reason:
        kwargs['reason'] = u'foo'
    br.reject(**kwargs)
    assert br.state == BlockedRoom.State.rejected
    mail = extract_emails(smtp, one=True, to=dummy_blocking.created_by_user.email, subject='Room blocking REJECTED')
    if with_reason:
        assert kwargs['reason'] in mail.as_string()
    assert not smtp.outbox


@pytest.mark.parametrize(('notify_blocker', 'colliding_reservation', 'colliding_occurrence'),
                         bool_matrix('...'))
def test_approve(create_user, create_reservation, create_blocking, smtp,
                 notify_blocker, colliding_reservation, colliding_occurrence):
    blocking = create_blocking(start_date=date.today(),
                               end_date=date.today() + timedelta(days=1))
    br = blocking.blocked_rooms[0]
    other_user = create_user(123)
    resv = create_reservation(start_dt=datetime.combine(blocking.start_date, time(8)),
                              end_dt=datetime.combine(blocking.start_date, time(10)),
                              created_by_user=other_user if colliding_reservation else blocking.created_by_user,
                              booked_for_user=other_user if colliding_reservation else blocking.created_by_user)
    resv2 = create_reservation(start_dt=datetime.combine(blocking.start_date + timedelta(days=1), time(8)),
                               end_dt=datetime.combine(blocking.end_date + timedelta(days=1), time(10)),
                               repeat_frequency=RepeatFrequency.DAY,
                               created_by_user=other_user if colliding_occurrence else blocking.created_by_user,
                               booked_for_user=other_user if colliding_occurrence else blocking.created_by_user)
    assert br.state == BlockedRoom.State.pending
    br.approve(notify_blocker=notify_blocker)
    assert br.state == BlockedRoom.State.accepted
    assert resv.is_rejected == colliding_reservation
    assert not resv2.is_rejected
    for occ in resv2.occurrences:
        assert occ.is_rejected == (colliding_occurrence and blocking.is_active_at(occ.date))
    if notify_blocker:
        extract_emails(smtp, one=True, to=blocking.created_by_user.email, subject='Room blocking ACCEPTED')
    assert len(smtp.outbox) == 2 * (colliding_occurrence + colliding_reservation)  # 2 emails per rejection


@pytest.mark.parametrize(('in_acl', 'rejected'), (
    (True,  False),
    (False, True)
))
def test_approve_acl(db, create_user, create_reservation, create_blocking, smtp, in_acl, rejected):
    other_user = create_user(123)
    blocking = create_blocking(start_date=date.today(),
                               end_date=date.today() + timedelta(days=1))
    if in_acl:
        blocking.allowed.add(other_user)
        db.session.flush()
    br = blocking.blocked_rooms[0]
    resv = create_reservation(start_dt=datetime.combine(blocking.start_date, time(8)),
                              end_dt=datetime.combine(blocking.start_date, time(10)),
                              created_by_user=other_user,
                              booked_for_user=other_user)
    assert br.state == BlockedRoom.State.pending
    br.approve(notify_blocker=False)
    assert br.state == BlockedRoom.State.accepted
    assert resv.is_rejected == rejected
    assert len(smtp.outbox) == (2 if rejected else 0)
