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

import {validator as v} from 'redux-router-querystring';


function _boolStateField(name) {
    return {
        serialize: ({filters: {[name]: value}}) => value || null,
        parse: (value, state) => {
            if (!state.filters) {
                state.filters = {};
            }
            state.filters[name] = value;
        }
    };
}


export const queryString = {
    recurrence: {
        validator: v.isIn(['single', 'daily', 'every']),
        stateField: 'filters.recurrence.type'
    },
    number: {
        validator: v.isInt({min: 1, max: 99}),
        sanitizer: v.toInt(),
        stateField: 'filters.recurrence.number'
    },
    interval: {
        validator: v.isIn(['week', 'month']),
        stateField: 'filters.recurrence.interval'
    },
    sd: {
        validator: v.isDate(),
        stateField: 'filters.dates.startDate'
    },
    ed: {
        validator: v.isDate(),
        stateField: 'filters.dates.endDate'
    },
    st: {
        validator: v.isTime(),
        stateField: 'filters.timeSlot.startTime'
    },
    et: {
        validator: v.isTime(),
        stateField: 'filters.timeSlot.endTime'
    },
    favorite: {
        validator: v.isBoolean(),
        sanitizer: v.toBoolean(),
        stateField: _boolStateField('onlyFavorites')
    },
    mine: {
        validator: v.isBoolean(),
        sanitizer: v.toBoolean(),
        stateField: _boolStateField('onlyMine')
    },
    capacity: {
        validator: v.isInt({min: 1}),
        sanitizer: v.toInt(),
        stateField: 'filters.capacity'
    },
    eq: {
        validator: () => true,
        stateField: {
            serialize: ({filters: {equipment}}) => Object.keys(equipment).filter(k => !!equipment[k]),
            parse: (value, state) => {
                if (!Array.isArray(value)) {
                    value = [value];
                }
                if (!state.filters) {
                    state.filters = {};
                }
                state.filters.equipment = Object.assign(...value.map(e => ({[e]: true})));
            }
        }
    },
    building: {
        stateField: 'filters.building'
    },
    floor: {
        stateField: 'filters.floor'
    },
    text: {
        stateField: 'filters.text'
    },
    sw_lat: {
        validator: v.isFloat({min: -90, max: 90}),
        sanitizer: v.toFloat(),
        stateField: 'filters.bounds.SW[0]'
    },
    sw_lng: {
        validator: v.isFloat({min: -180, max: 180}),
        sanitizer: v.toFloat(),
        stateField: 'filters.bounds.SW[1]'
    },
    ne_lat: {
        validator: v.isFloat({min: -90, max: 90}),
        sanitizer: v.toFloat(),
        stateField: 'filters.bounds.NE[0]'
    },
    ne_lng: {
        validator: v.isFloat({min: -180, max: 180}),
        sanitizer: v.toFloat(),
        stateField: 'filters.bounds.NE[1]'
    }
};

const _dtHandler = (prefix) => {
    return function({dates, timeSlot}) {
        const timePart = timeSlot[`${prefix}Time`];
        let datePart = dates[`${prefix}Date`];

        // single bookings have a 'null' endDate
        if (datePart === null && prefix === 'end') {
            datePart = dates['startDate'];
        }

        return moment(`${datePart} ${timePart}`, 'YYYY-MM-DD HH:mm').format('YYYY-MM-DD HH:mm');
    };
};

export const ajax = {
    repeat_frequency: {
        onlyIf: (data) => 'recurrence' in data,
        serializer: ({recurrence: {type, interval}}) => {
            if (type === 'single') {
                return 'NEVER';
            } else if (type === 'daily') {
                return 'DAY';
            } else {
                return {
                    week: 'WEEK',
                    month: 'MONTH'
                }[interval];
            }
        }
    },
    repeat_interval: {
        onlyIf: (data) => 'recurrence' in data,
        serializer: ({recurrence: {type, number}}) => {
            if (type === 'single') {
                return 0;
            } else if (type === 'daily') {
                return 1;
            } else {
                return number;
            }
        }
    },
    capacity: ({capacity}) => capacity,
    favorite: {
        onlyIf: ({onlyFavorites}) => onlyFavorites,
        serializer: ({onlyFavorites}) => onlyFavorites,
    },
    mine: {
        onlyIf: ({onlyMine}) => onlyMine,
        serializer: ({onlyMine}) => onlyMine,
    },
    equipment: ({equipment}) => Object.keys(equipment).filter(k => !!equipment[k]),
    building: ({building}) => building,
    floor: ({floor}) => floor,
    text: ({text}) => text,
    start_dt: {
        onlyIf: (data) => data.dates && data.dates.startDate,
        serializer: _dtHandler('start')
    },
    end_dt: {
        onlyIf: (data) => data.dates,
        serializer: _dtHandler('end')
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
    }
};
