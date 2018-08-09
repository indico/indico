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

import moment from 'moment';
import * as actions from '../../actions';
import {parseSearchBarText, sanitizeRecurrence} from '../../util';


export const initialStateFactory = (namespace) => {
    const state = {
        text: null,
        capacity: null,
        onlyFavorites: false,
        onlyMine: false,
        equipment: []
    };

    if (namespace === 'bookRoom') {
        Object.assign(state, {
            recurrence: {
                type: null,
                number: null,
                interval: null
            },
            dates: {
                startDate: null,
                endDate: null
            },
            timeSlot: {
                startTime: null,
                endTime: null
            },
            bounds: null
        });
    } else if (namespace === 'roomList') {
        Object.assign(state, {
            building: null,
            floor: null
        });
    } else if (namespace === 'blockingList') {
        Object.assign(state, {
            myBlockings: false,
            blockingsInMyRooms: false,
            dates: {
                startDate: moment().format('YYYY-MM-DD'),
                endDate: null
            }
        });
    }

    return state;
};

function mergeFilter(filters, param, data) {
    const newFilters = {...filters, [param]: data};
    if (param === 'recurrence') {
        sanitizeRecurrence(newFilters);
    } else if (param === 'text') {
        const dd = parseSearchBarText(data);
        newFilters.text = dd.text || null;
        newFilters.building = dd.building || null;
        newFilters.floor = dd.floor || null;
    }

    return newFilters;
}

export default function filterReducerFactory(namespace) {
    return (state = initialStateFactory(namespace), action) => {
        switch (action.type) {
            case actions.SET_FILTER_PARAMETER:
                return action.namespace === namespace ? mergeFilter(state, action.param, action.data) : state;
            case actions.SET_FILTERS:
                return action.namespace === namespace ? action.params : state;
            case actions.RESET_PAGE_STATE:
                return (!action.namespace || action.namespace === namespace) ? initialStateFactory(namespace) : state;
            default:
                return state;
        }
    };
}
