/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

import {filterDTHandler} from '../../serializers/common';


export const ajax = {
    my_rooms: {
        onlyIf: ({myRooms}) => myRooms,
        serializer: ({myRooms}) => myRooms,
    },
    mine: {
        onlyIf: ({myBlockings}) => myBlockings,
        serializer: ({myBlockings}) => myBlockings,
    },
    room_ids: {
        onlyIf: ({rooms}) => rooms && rooms.length,
        serializer: ({rooms}) => rooms.map((room) => room.id)
    },
    allowed_principals: {
        onlyIf: ({allowed}) => !!allowed,
        serializer: ({allowed}) => allowed.map((obj) => ({
            id: obj.id, is_group: obj.is_group, provider: obj.provider, name: obj.name
        }))
    },
    reason: ({reason}) => reason,
    start_date: filterDTHandler('start'),
    end_date: filterDTHandler('end'),
};
