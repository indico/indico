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

import {
    filterDTHandler, recurrenceIntervalSerializer, recurrenceFrequencySerializer
} from '../../serializers';


export const ajax = {
    start_dt: filterDTHandler('start'),
    end_dt: filterDTHandler('end'),
    repeat_frequency: recurrenceFrequencySerializer,
    repeat_interval: recurrenceIntervalSerializer,
    reason: ({reason}) => reason,
    user_id: {
        onlyIf: ({usage}) => usage === 'someone',
        serializer: ({user: {id}}) => id
    },
    room_id: ({room: {id}}) => id,
    is_prebooking: ({isPrebooking}) => isPrebooking,
    link_type: ({linkType}) => linkType,
    link_id: ({linkId}) => linkId,
    link_back: ({linkBack}) => linkBack,
    extra_fields: ({extraFields}) => extraFields,
};
