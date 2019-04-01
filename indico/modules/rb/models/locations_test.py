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

from indico.modules.rb.models.rooms import Room


pytest_plugins = 'indico.modules.rb.testing.fixtures'


def test_room_name_format(create_location, db, dummy_user):
    location = create_location(u'Foo')
    location.room_name_format = '{building}|{floor}|{number}'
    assert location._room_name_format == '%1$s|%2$s|%3$s'

    Room(building=1, floor=2, number=3, verbose_name='First amphitheater', location=location, owner=dummy_user)
    Room(building=1, floor=3, number=4, verbose_name='Second amphitheater', location=location, owner=dummy_user)
    Room(building=1, floor=2, number=4, verbose_name='Room 3', location=location, owner=dummy_user)
    db.session.flush()
    assert Room.query.filter(Room.full_name.contains('|3')).count() == 2
