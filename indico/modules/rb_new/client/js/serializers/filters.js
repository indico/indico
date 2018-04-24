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
        validator: v.isIn(['day', 'week', 'month']),
        stateField: 'filters.recurrence.interval'
    },
    startDate: {
        validator: v.isDate(),
        stateField: 'filters.dates.startDate'
    },
    endDate: {
        validator: v.isDate(),
        stateField: 'filters.dates.endDate'
    },
    startTime: {
        validator: v.isTime(),
        stateField: 'filters.timeSlot.startTime'
    },
    endTime: {
        validator: v.isTime(),
        stateField: 'filters.timeSlot.endTime'
    },
    capacity: {
        validator: v.isInt({min: 1}),
        sanitizer: v.toInt(),
        stateField: 'filters.capacity'
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

        return moment(`${datePart} ${timePart}`, 'YYYY-MM-DD HH:mm').toISOString(true);
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
                    daily: 'DAY',
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
    start_dt: {
        onlyIf: (data) => 'dates' in data,
        serializer: _dtHandler('start')
    },
    end_dt: {
        onlyIf: (data) => 'dates' in data,
        serializer: _dtHandler('end')
    }
};
