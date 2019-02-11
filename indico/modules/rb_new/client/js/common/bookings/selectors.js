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
import moment from 'moment';
import {createSelector} from 'reselect';
import {RequestState} from 'indico/utils/redux';
import {selectors as roomsSelectors} from '../rooms';
import {isUserAdminOverrideEnabled} from '../user/selectors';


const getRawDetails = (state, {bookingId}) => state.bookings.details[bookingId];


function applyPermissionsToOccurrences(occurrences, override) {
    return _.fromPairs(Object.entries(occurrences).map(([key, data]) => {
        data = _.fromPairs(Object.entries(data).map(([day, dayData]) => {
            dayData = dayData.map(rawOcc => {
                const {permissions, ...occ} = rawOcc;
                if (!permissions) {
                    return occ;
                }
                const activePermissions = (override && permissions.admin) ? permissions.admin : permissions.user;
                return {...occ, ...activePermissions};
            });
            return [day, dayData];
        }));
        return [key, data];
    }));
}

export const getDetails = createSelector(
    getRawDetails,
    isUserAdminOverrideEnabled,
    (allDetails, override) => {
        if (!allDetails) {
            // details not loaded yet, just keep the null/undefined
            return allDetails;
        }
        const {permissions, occurrences, ...details} = allDetails;
        const activePermissions = (override && permissions.admin) ? permissions.admin : permissions.user;
        const occurrencesWithPermissions = applyPermissionsToOccurrences(occurrences, override);
        return {...details, ...activePermissions, occurrences: occurrencesWithPermissions};
    }
);


export const getDetailsWithRoom = createSelector(
    getDetails,
    roomsSelectors.getAllRooms,
    (booking, allRooms) => {
        return {...booking, room: allRooms[booking.roomId]};
    }
);
export const hasDetails = (state, {bookingId}) => getDetails(state, {bookingId}) !== undefined;
export const isBookingChangeInProgress = ({bookings}) => (
    bookings.requests.changePrebookingState.state === RequestState.STARTED
);
export const isOngoingBooking = createSelector(
    getDetailsWithRoom,
    ({startDt, endDt}) => {
        return moment().isBetween(startDt, endDt, 'day');
    },
);
export const getNumberOfBookingOccurrences = createSelector(
    getDetailsWithRoom,
    ({occurrences: {bookings}}) => {
        return Object.values(bookings).reduce((acc, cur) => acc + (cur.length ? 1 : 0), 0);
    },
);
