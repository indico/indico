# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import pytest

from indico.modules.users import User


pytest_plugins = 'indico.modules.rb.testing.fixtures'


@pytest.mark.parametrize('bulk_possible', (True, False))
def test_managed_rooms(monkeypatch, bulk_possible, create_user, create_room, dummy_user):
    from indico.modules.rb.operations.rooms import get_managed_room_ids
    monkeypatch.setattr(User, 'can_get_all_multipass_groups', bulk_possible)

    users = {
        'x': {'first_name': 'Regular', 'last_name': 'User'},
        'y': {'first_name': 'Room', 'last_name': 'Owner'},
        'z': {'first_name': 'ManyRooms', 'last_name': 'Owner'}
    }

    rooms = {
        'a': {'verbose_name': 'Red room', 'owner': 'z'},
        'b': {'verbose_name': 'Blue room', 'owner': 'y'},
        'c': {'verbose_name': 'Green room', 'owner': 'y'}
    }

    user_map = {key: create_user(id_, **data) for id_, (key, data) in enumerate(users.iteritems(), 1)}
    room_map = {}
    for id_, (key, data) in enumerate(rooms.iteritems(), 1):
        data['id'] = id_
        data['owner'] = user_map[data['owner']]
        room_map[key] = create_room(**data)

    room_map['a'].update_principal(user_map['y'], full_access=True)

    for key, user in user_map.iteritems():
        room_ids = [room.id for room in room_map.values() if (room.owner == user_map[key] or room.can_manage(user))]
        assert get_managed_room_ids(user) == set(room_ids)
