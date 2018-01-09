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

from __future__ import unicode_literals

from datetime import timedelta

import pytest

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
