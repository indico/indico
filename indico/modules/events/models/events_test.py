# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from datetime import date, datetime, time, timedelta

import pytest
import pytz

from indico.core.db.sqlalchemy.protection import ProtectionMode
from indico.modules.events import Event
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.sessions import Session


def test_deleted_relationships(db, dummy_event):
    event = dummy_event
    assert not event.contributions
    assert not event.sessions
    s = Session(event=event, title='s')
    sd = Session(event=event, title='sd', is_deleted=True)
    c = Contribution(event=event, title='c', session=sd, duration=timedelta(minutes=30))
    cd = Contribution(event=event, title='cd', session=sd, duration=timedelta(minutes=30), is_deleted=True)
    sc = SubContribution(contribution=c, title='sc', duration=timedelta(minutes=10))
    scd = SubContribution(contribution=c, title='scd', duration=timedelta(minutes=10), is_deleted=True)
    db.session.flush()
    db.session.expire_all()
    # reload all the objects from the db
    event = Event.get(event.id)
    s = Session.get(s.id)
    sd = Session.get(sd.id)
    c = Contribution.get(c.id)
    cd = Contribution.get(cd.id)
    sc = SubContribution.get(sc.id)
    scd = SubContribution.get(scd.id)
    # deleted items should not be in the lists
    assert event.sessions == [s]
    assert event.contributions == [c]
    assert sd.contributions == [c]
    assert c.subcontributions == [sc]
    # the other direction should work fine even in case of deletion
    assert s.event == event
    assert sd.event == event
    assert c.event == event
    assert cd.event == event
    assert sc.contribution == c
    assert scd.contribution == c


def test_modify_relationship_with_deleted(db, dummy_event):
    event = dummy_event
    c = Contribution(event=event, title='c', duration=timedelta(minutes=30))
    cd = Contribution(event=event, title='cd', duration=timedelta(minutes=30), is_deleted=True)
    db.session.flush()
    assert event.contributions == [c]
    c2 = Contribution(title='c2', duration=timedelta(minutes=30))
    # this should hard-delete c but not touch cd since it's not in the relationship
    event.contributions = [c2]
    db.session.flush()
    assert set(Contribution.find_all()) == {cd, c2}


@pytest.mark.parametrize(('category_pm', 'event_pm', 'effective_pm'), (
    (ProtectionMode.inheriting, ProtectionMode.inheriting, ProtectionMode.public),
    (ProtectionMode.protected, ProtectionMode.inheriting, ProtectionMode.protected),
    (ProtectionMode.public, ProtectionMode.inheriting, ProtectionMode.public),
    (ProtectionMode.protected, ProtectionMode.public, ProtectionMode.public),
    (ProtectionMode.public, ProtectionMode.protected, ProtectionMode.protected)
))
def test_effective_protection_mode(db, dummy_category, dummy_event, category_pm, event_pm, effective_pm):
    dummy_category.protection_mode = category_pm
    dummy_event.protection_mode = event_pm
    db.session.flush()
    assert dummy_event.effective_protection_mode == effective_pm


@pytest.mark.parametrize('tz', ('UTC', 'Europe/Zurich'))
@pytest.mark.parametrize(('start_dt', 'end_dt', 'days'), (
    (datetime(2019, 8, 16, 10, 0), datetime(2019, 8, 16, 15, 0), [date(2019, 8, 16)]),
    (datetime(2019, 8, 16, 10, 0), datetime(2019, 8, 17, 15, 0), [date(2019, 8, 16), date(2019, 8, 17)]),
    (datetime(2019, 8, 16, 10, 0), datetime(2019, 8, 17, 8, 0), [date(2019, 8, 16), date(2019, 8, 17)]),
    (datetime(2019, 8, 16, 0, 0), datetime(2019, 8, 17, 0, 0), [date(2019, 8, 16), date(2019, 8, 17)]),
    (datetime(2020, 9, 24, 12, 0), datetime(2020, 9, 25, 14, 0), [date(2020, 9, 24), date(2020, 9, 25)]),
))
def test_iter_days(dummy_event, tz, start_dt, end_dt, days):
    tzinfo = pytz.timezone(tz)
    dummy_event.start_dt = tzinfo.localize(start_dt)
    dummy_event.end_dt = tzinfo.localize(end_dt)
    assert list(dummy_event.iter_days()) == days


@pytest.mark.parametrize('tz', ('UTC', 'Europe/Zurich'))
@pytest.mark.parametrize(('start_time', 'end_time'), (
    (time(0), time(0)),
    (time(1), time(1)),
    (time(1), time(2)),
    (time(2), time(2)),
    (time(12), time(14)),
    (time(22), time(22)),
    (time(22), time(23)),
    (time(23), time(23)),
))
@pytest.mark.parametrize(('start_date', 'end_date', 'days'), (
    # no dst change
    (date(2020, 9, 24), date(2020, 9, 25), [date(2020, 9, 24), date(2020, 9, 25)]),
    # one dst change (UTC+1 to UTC+2)
    (date(2020, 3, 28), date(2020, 3, 29), [date(2020, 3, 28), date(2020, 3, 29)]),
    # one dst change (UTC+2 to UTC+1)
    (date(2020, 10, 24), date(2020, 10, 25), [date(2020, 10, 24), date(2020, 10, 25)]),
    # two dst changes
    (date(2020, 10, 24), date(2021, 3, 30), [date(2020, 10, 24), date(2021, 3, 30)]),
))
def test_iter_days_dst(dummy_event, tz, start_time, end_time, start_date, end_date, days):
    start_dt = datetime.combine(start_date, start_time)
    end_dt = datetime.combine(end_date, end_time)
    tzinfo = pytz.timezone(tz)
    dummy_event.start_dt = tzinfo.localize(start_dt)
    dummy_event.end_dt = tzinfo.localize(end_dt)
    all_days = list(dummy_event.iter_days())
    assert all_days[0] == days[0]
    assert all_days[-1] == days[-1]
