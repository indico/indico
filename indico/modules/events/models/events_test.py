# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from indico.modules.events import Event
from indico.modules.events.contributions import Contribution
from indico.modules.events.contributions.models.subcontributions import SubContribution
from indico.modules.events.sessions import Session


def test_deleted_relationships(db, dummy_event_new):
    event = dummy_event_new
    assert not event.contributions.count()
    assert not event.sessions.count()
    s = Session(event_new=event, title='s')
    sd = Session(event_new=event, title='sd', is_deleted=True)
    c = Contribution(event_new=event, title='c', session=sd, duration=timedelta(minutes=30))
    cd = Contribution(event_new=event, title='cd', session=sd, duration=timedelta(minutes=30), is_deleted=True)
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
    assert event.sessions.all() == [s]
    assert event.contributions.all() == [c]
    assert sd.contributions == [c]
    assert c.subcontributions == [sc]
    # the other direction should work fine even in case of deletion
    assert s.event_new == event
    assert sd.event_new == event
    assert c.event_new == event
    assert cd.event_new == event
    assert sc.contribution == c
    assert scd.contribution == c


def test_modify_relationship_with_deleted(db, dummy_event_new):
    event = dummy_event_new
    c = Contribution(event_new=event, title='c', duration=timedelta(minutes=30))
    cd = Contribution(event_new=event, title='cd', duration=timedelta(minutes=30), is_deleted=True)
    db.session.flush()
    assert event.contributions.all() == [c]
    c2 = Contribution(title='c2', duration=timedelta(minutes=30))
    # this should hard-delete c but not touch cd since it's not in the relationship
    event.contributions = [c2]
    db.session.flush()
    assert set(Contribution.find_all()) == {cd, c2}
