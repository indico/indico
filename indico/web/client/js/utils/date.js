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


export function toMoment(dt, format) {
    return dt ? moment(dt, format) : null;
}

export function serializeDate(dt, format = moment.HTML5_FMT.DATE) {
    return dt ? moment(dt).format(format) : null;
}

export function serializeTime(dt, format = moment.HTML5_FMT.TIME) {
    return dt ? moment(dt).format(format) : null;
}

export async function setMomentLocale(locale) {
    const [language, territory] = locale.toLowerCase().split('_');
    let momentLocale;

    if (language === territory) {
        momentLocale = language;
    } else {
        momentLocale = `${language}-${territory}`;
    }

    if (momentLocale !== 'en') {
        await import(`moment/locale/${momentLocale}`);
    }
    moment.locale(momentLocale);
}

export function dayRange(start, end, step = 1) {
    const next = start.clone();
    const result = [];
    while (next.isSameOrBefore(end)) {
        result.push(next.clone());
        next.add(step, 'd');
    }
    return result;
}

export function createDT(date, time) {
    const momentDate = moment(date, 'YYYY-MM-DD');
    const momentTime = moment(time, 'HH:mm');
    if (!momentDate.isValid() || !momentTime.isValid()) {
        return null;
    }

    return moment([...momentDate.toArray().splice(0, 3), ...momentTime.toArray().splice(3)]);
}

function isBookingStartValid(dt, isAdminOverrideEnabled = false, granularity = 'minute') {
    if (!dt || !dt.isValid()) {
        return false;
    } else if (isAdminOverrideEnabled) {
        return true;
    }
    const gracePeriod = granularity === 'day' ? moment() : moment().subtract(1, 'hour');
    return dt.isSameOrAfter(gracePeriod, granularity);
}

export function isBookingStartDateValid(date, isAdminOverrideEnabled) {
    return isBookingStartValid(date, isAdminOverrideEnabled, 'day');
}

export function isBookingStartDTValid(dt, isAdminOverrideEnabled) {
    return isBookingStartValid(dt, isAdminOverrideEnabled);
}
