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

export function parseSearchBarText(text) {
    const result = {text: null, building: null, floor: null};
    if (!text) {
        return result;
    }

    const parts = text.split(' ');
    for (const item of parts) {
        if (!item) {
            continue;
        }

        const [filter, value] = item.trimRight().split(':');
        if (value && ['bldg', 'floor'].includes(filter)) {
            result[filter !== 'bldg' ? filter : 'building'] = value;
        } else {
            result.text = item ? item.trim() : null;
        }
    }

    return result;
}

export function preProcessParameters(params, rules) {
    return _pruneNullLeaves(
        Object.assign(...Object.entries(rules)
            .map(([k, rule]) => {
                if (typeof rule === 'object') {
                    const {serializer, onlyIf} = rule;
                    rule = serializer;
                    if (!onlyIf(params)) {
                        return {};
                    }
                }
                const value = rule(params);
                return {[k]: value};
            }))
    );
}

function calculateDefaultEndDate(startDate, type, number, interval) {
    const isMoment = moment.isMoment(startDate);
    const dt = isMoment ? startDate.clone() : moment(startDate);

    console.log(dt);

    if (type === 'daily') {
        dt.add(1, 'weeks');
    } else if (interval === 'week') {
        // 5 occurrences
        dt.add(4 * number, 'weeks');
    } else {
        // 7 occurences
        dt.add(6 * number, 'months');
    }
    console.log(dt);
    return isMoment ? dt : dt.format('YYYY-MM-DD');
}

export function sanitizeRecurrence(filters) {
    const {dates: {endDate, startDate}, recurrence: {type, interval, number}} = filters;

    if (type === 'single' && endDate) {
        filters.dates.endDate = null;
    } else if (type !== 'single' && startDate && !endDate) {
        // if there's a start date already set, let's set a sensible
        // default for the end date
        filters.dates.endDate = calculateDefaultEndDate(startDate, type, number, interval);
    }
}

export function getAspectBounds(aspect) {
    return [
        [aspect.top_left_latitude, aspect.top_left_longitude],
        [aspect.bottom_right_latitude, aspect.bottom_right_longitude]
    ];
}

export function getMapBounds(map) {
    const boundsObj = map.getBounds();
    return [
        Object.values(boundsObj.getNorthWest()),
        Object.values(boundsObj.getSouthEast())
    ];
}

function _pruneNullLeaves(obj) {
    return Object.assign(...Object.entries(obj).map(([k, v]) => {
        if (v === null) {
            return {};
        } else if (typeof v === 'object') {
            return {[k]: _pruneNullLeaves(v)};
        } else {
            return {[k]: v};
        }
    }));
}
