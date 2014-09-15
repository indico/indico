## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.
from datetime import date, timedelta, datetime

import pytest

from indico.modules.rb.models.blocked_rooms import BlockedRoom


pytest_plugins = 'indico.modules.rb.testing.fixtures'


@pytest.mark.parametrize('state', BlockedRoom.State)
def test_state_name(state):
    assert BlockedRoom(state=state).state_name == state.title


def test_find_with_filters(create_room, create_blocking):
    rooms = [create_room(), create_room()]
    blockings = [
        create_blocking(start_date=date.today(),
                        end_date=date.today(),
                        room=rooms[0],
                        state=BlockedRoom.State.accepted),
        create_blocking(start_date=date.today() + timedelta(days=1),
                        end_date=date.today() + timedelta(days=1),
                        room=rooms[1]),
        create_blocking(start_date=date.today() + timedelta(days=1),
                        end_date=date.today() + timedelta(days=1),
                        room=rooms[1]),
    ]
    assert set(BlockedRoom.find_with_filters({})) == set(b.blocked_rooms[0] for b in blockings)
    filters = {'start_date': date.today(),
               'end_date': date.today(),
               'room_ids': {rooms[0].id},
               'state': BlockedRoom.State.accepted}
    assert set(BlockedRoom.find_with_filters(filters)) == {blockings[0].blocked_rooms[0]}


@pytest.mark.parametrize(('start_date', 'end_date', 'matches'), (
    ('2014-12-05', '2014-12-08', {0, 1}),
    ('2014-12-04', '2014-12-09', {0, 1}),
    ('2014-12-07', '2014-12-07', {0, 1}),
    ('2014-12-05', '2014-12-05', {0}),
    ('2014-12-08', '2014-12-08', {1}),
    ('2014-12-10', '2014-12-10', set()),
))
def test_find_with_filters_dates(create_blocking, start_date, end_date, matches):
    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    blockings = [
        create_blocking(start_date=date(2014, 12, 5), end_date=date(2014, 12, 7)),
        create_blocking(start_date=date(2014, 12, 6), end_date=date(2014, 12, 8))
    ]
    filters = {'start_date': start_date,
               'end_date': end_date}
    assert set(BlockedRoom.find_with_filters(filters)) == set(blockings[i].blocked_rooms[0] for i in matches)


@pytest.mark.parametrize('state', BlockedRoom.State)
def test_find_with_filters_state(create_blocking, state):
    other_state = next(s for s in BlockedRoom.State if s != state)
    create_blocking(state=other_state)
    blocking = create_blocking(state=state)
    assert set(BlockedRoom.find_with_filters({'state': state})) == {blocking.blocked_rooms[0]}
