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

import {filterDTHandler, recurrenceFrequencySerializer, recurrenceIntervalSerializer} from '../../serializers';


export const ajax = {
    repeat_frequency: recurrenceFrequencySerializer,
    repeat_interval: recurrenceIntervalSerializer,
    capacity: ({capacity}) => capacity,
    favorite: {
        onlyIf: ({onlyFavorites}) => onlyFavorites,
        serializer: ({onlyFavorites}) => onlyFavorites
    },
    equipment: {
        onlyIf: ({equipment}) => equipment && equipment.length,
        serializer: ({equipment}) => equipment
    },
    feature: {
        onlyIf: ({features}) => features && features.length,
        serializer: ({features}) => features
    },
    mine: {
        onlyIf: ({onlyMine}) => onlyMine,
        serializer: ({onlyMine}) => onlyMine,
    },
    building: ({building}) => building,
    text: ({text}) => text,
    division: ({division}) => division,
    start_dt: {
        onlyIf: (data) => data.dates && data.dates.startDate,
        serializer: filterDTHandler('start')
    },
    end_dt: {
        onlyIf: (data) => data.dates,
        serializer: filterDTHandler('end')
    },
    sw_lat: {
        onlyIf: (data) => data.bounds && 'SW' in data.bounds,
        serializer: ({bounds: {SW}}) => SW[0]
    },
    sw_lng: {
        onlyIf: (data) => data.bounds && 'SW' in data.bounds,
        serializer: ({bounds: {SW}}) => SW[1]
    },
    ne_lat: {
        onlyIf: (data) => data.bounds && 'NE' in data.bounds,
        serializer: ({bounds: {NE}}) => NE[0]
    },
    ne_lng: {
        onlyIf: (data) => data.bounds && 'NE' in data.bounds,
        serializer: ({bounds: {NE}}) => NE[1]
    },
};
