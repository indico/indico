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
