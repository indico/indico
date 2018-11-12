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

import _ from 'lodash';
import LatLon from 'geodesy/latlon-vectors';


export function getAreaBounds(area) {
    return {
        SW: [area.top_left_latitude, area.top_left_longitude],
        NE: [area.bottom_right_latitude, area.bottom_right_longitude]
    };
}


export function getMapBounds(map) {
    const boundsObj = map.getBounds();
    return {
        SW: Object.values(boundsObj.getSouthWest()),
        NE: Object.values(boundsObj.getNorthEast())
    };
}


/** Calculate a bounding box that encompasses all the rooms provided in an array. */
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

/** Return something like xx°yy′zz″N, ... */
export function formatLatLon(lat, lon) {
    return new LatLon(lat, lon).toString('dms', 2);
}
