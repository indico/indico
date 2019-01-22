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
import {createSelector} from 'reselect';
import {RequestState} from 'indico/utils/redux';
import {selectors as roomsSelectors} from '../../common/rooms';
import {selectors as userSelectors} from '../../common/user';


const CALENDAR_FILTERS = ['myBookings'];
const LOCAL_FILTERS = ['hideUnused', 'onlyAuthorized'];
export const getFilters = ({calendar}) => calendar.filters;

export const getRoomFilters = createSelector(
    getFilters,
    filters => _.omit(filters, [...CALENDAR_FILTERS, ...LOCAL_FILTERS])
);
export const getCalendarFilters = createSelector(
    getFilters,
    filters => _.pick(filters, CALENDAR_FILTERS)
);
export const getLocalFilters = createSelector(
    getFilters,
    filters => _.pick(filters, LOCAL_FILTERS)
);

export const isFetchingCalendar = ({calendar}) => calendar.requests.calendar.state === RequestState.STARTED;
export const getDatePickerInfo = ({calendar}) => calendar.datePicker;
export const getCalendarData = createSelector(
    ({calendar: {data}}) => data,
    roomsSelectors.getAllRooms,
    getLocalFilters,
    userSelectors.getUnbookableRoomIds,
    ({roomIds, rows}, allRooms, {onlyAuthorized}, unbookableRoomIds) => {
        if (onlyAuthorized) {
            const unbookable = new Set(unbookableRoomIds);
            roomIds = roomIds.filter(id => !unbookable.has(id));
            rows = rows.filter(({roomId}) => !unbookable.has(roomId));
        }
        return {
            roomIds,
            rows: rows.map(entry => {
                const room = allRooms[entry.roomId];
                return [
                    room.id,
                    {...entry, room}
                ];
            })
        };
    }
);

export const getNumberOfRowsLeft = ({calendar}) => calendar.activeBookings.rowsLeft;
export const isFetchingActiveBookings = ({calendar}) => calendar.requests.activeBookings.state === RequestState.STARTED;
export const getActiveBookings = createSelector(
    ({calendar}) => calendar.activeBookings.data,
    roomsSelectors.getAllRooms,
    getLocalFilters,
    userSelectors.getUnbookableRoomIds,
    (activeBookings, allRooms, {onlyAuthorized}, unbookableRoomIds) => {
        const unbookable = new Set(unbookableRoomIds);
        return _.fromPairs(Object.entries(activeBookings).map(([day, dayActiveBookings]) => {
            if (onlyAuthorized) {
                dayActiveBookings = dayActiveBookings.filter(({reservation: {roomId}}) => !unbookable.has(roomId));
            }
            const bookingsWithRooms = dayActiveBookings.map((dayActiveBooking) => {
                const roomId = dayActiveBooking.reservation.roomId;
                const {reservation} = dayActiveBooking;
                return {...dayActiveBooking, reservation: {...reservation, room: allRooms[roomId]}};
            });
            return [day, bookingsWithRooms];
        }));
    },
);

export const getCalendarView = ({calendar}) => calendar.view;
