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

export const filterDTHandler = (prefix) => {
    return function({dates, timeSlot}) {
        const timePart = timeSlot === undefined ? '' : timeSlot[`${prefix}Time`];
        let datePart = dates[`${prefix}Date`];

        // single bookings have a 'null' endDate
        if (datePart === null && prefix === 'end') {
            datePart = dates['startDate'];
        }

        return `${datePart} ${timePart || ''}`.trimRight();
    };
};

export const recurrenceFrequencySerializer = {
    onlyIf: (data) => data.recurrence && data.recurrence.interval && data.recurrence.type,
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
};

export const recurrenceIntervalSerializer = {
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
};
