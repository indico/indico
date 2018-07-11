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

import React from 'react';
import {push} from 'connected-react-router';
import LatLon from 'geodesy/latlon-vectors';
import moment from 'moment';
import {Dimmer} from 'semantic-ui-react';
import {Preloader} from 'indico/react/util';


export function toMoment(dt, format) {
    return dt ? moment(dt, format) : null;
}

export function serializeTime(time) {
    return time ? time.format('HH:mm') : null;
}

export function parseSearchBarText(queryText) {
    const resultMap = {bldg: 'building', floor: 'floor'};
    const result = {text: null, building: null, floor: null};
    if (!queryText) {
        return result;
    }

    const parts = queryText.split(/\s+/).filter(x => !!x);
    const textParts = [];
    for (const item of parts) {
        const [filter, value] = item.split(':');
        if (value && resultMap.hasOwnProperty(filter)) {
            result[resultMap[filter]] = value;
        } else if (item) {
            textParts.push(item);
        }
    }

    result.text = textParts.join(' ').trim() || null;
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

    if (type === 'daily') {
        dt.add(1, 'weeks');
    } else if (interval === 'week') {
        // 5 occurrences
        dt.add(4 * number, 'weeks');
    } else {
        // 7 occurences
        dt.add(6 * number, 'months');
    }
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
    return {
        SW: [aspect.top_left_latitude, aspect.top_left_longitude],
        NE: [aspect.bottom_right_latitude, aspect.bottom_right_longitude]
    };
}

export function getMapBounds(map) {
    const boundsObj = map.getBounds();
    return {
        SW: Object.values(boundsObj.getSouthWest()),
        NE: Object.values(boundsObj.getNorthEast())
    };
}

/*
Calculate a bounding box that encompasses all the rooms provided in
an array.
*/
export function checkRoomsInBounds(rooms, bounds) {
    if (!rooms.length) {
        return null;
    }
    const polygon = [
        new LatLon(bounds.NE[0], bounds.NE[1]),
        new LatLon(bounds.NE[0], bounds.SW[1]),
        new LatLon(bounds.SW[0], bounds.SW[1]),
        new LatLon(bounds.SW[0], bounds.NE[1])
    ];

    return rooms.every(({lat, lng}) => new LatLon(lat, lng).enclosedBy(polygon));
}

export function getRoomListBounds(rooms) {
    if (!rooms.length) {
        return null;
    }
    const points = rooms.map(({lat, lng}) => new LatLon(lat, lng));
    const center = LatLon.meanOf(points);
    const farthest = _.max(points.map(p => center.distanceTo(p))) * 1.1;
    const sw = center.destinationPoint(farthest, 225);
    const ne = center.destinationPoint(farthest, 45);
    return {
        SW: [sw.lat, sw.lon],
        NE: [ne.lat, ne.lon]
    };
}

function _pruneNullLeaves(obj) {
    if (!Object.entries(obj).length) {
        return {};
    }

    return Object.assign(...Object.entries(obj).map(([k, v]) => {
        if (v === null) {
            return {};
        } else if (Array.isArray(v)) {
            return {[k]: v.filter(e => e !== null)};
        } else if (typeof v === 'object') {
            return {[k]: _pruneNullLeaves(v)};
        } else {
            return {[k]: v};
        }
    }));
}

export const pushStateMergeProps = (stateProps, dispatchProps, ownProps) => ({
    ...ownProps,
    ...stateProps,
    ...dispatchProps,
    pushState(url, restoreQueryString = false) {
        if (restoreQueryString) {
            url += `?${stateProps.queryString}`;
        }
        dispatchProps.dispatch(push(url));
    }
});


export const roomPreloader = (componentFunc, action) => {
    // eslint-disable-next-line react/display-name, react/prop-types
    return ({match: {params: {roomId}}}) => (
        <Preloader checkCached={({roomDetails: {rooms: cachedRooms}}) => !!cachedRooms[roomId]}
                   action={() => action(roomId)}
                   dimmer={<Dimmer page />}>
            {() => componentFunc(roomId)}
        </Preloader>
    );
};
