# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
