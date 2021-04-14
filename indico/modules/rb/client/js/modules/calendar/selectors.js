// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

import {RequestState} from 'indico/utils/redux';

import {selectors as roomsSelectors} from '../../common/rooms';
import {selectors as userSelectors} from '../../common/user';

const CALENDAR_FILTERS = ['myBookings', 'showInactive'];
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

export const isFetchingCalendar = ({calendar}) =>
  calendar.requests.calendar.state === RequestState.STARTED;
export const getDatePickerInfo = ({calendar}) => calendar.datePicker;
export const getCalendarData = createSelector(
  ({calendar: {data}}) => data,
  roomsSelectors.getAllRooms,
  getLocalFilters,
  getCalendarFilters,
  userSelectors.getUnbookableRoomIds,
  ({roomIds, rows}, allRooms, {onlyAuthorized}, {showInactive}, unbookableRoomIds) => {
    if (onlyAuthorized) {
      const unbookable = new Set(unbookableRoomIds);
      roomIds = roomIds.filter(id => !unbookable.has(id));
      rows = rows.filter(({roomId}) => !unbookable.has(roomId));
    }
    return {
      roomIds,
      rows: rows.map(entry => {
        const room = allRooms[entry.roomId];
        const newEntry = {...entry};

        if (!showInactive) {
          newEntry.cancellations = {};
          newEntry.rejections = {};
        }

        return [room.id, {...newEntry, room}];
      }),
    };
  }
);

export const getNumberOfRowsLeft = ({calendar}) => calendar.activeBookings.rowsLeft;
export const isFetchingActiveBookings = ({calendar}) =>
  calendar.requests.activeBookings.state === RequestState.STARTED;
export const getActiveBookings = createSelector(
  ({calendar}) => calendar.activeBookings.data,
  roomsSelectors.getAllRooms,
  getLocalFilters,
  userSelectors.getUnbookableRoomIds,
  (activeBookings, allRooms, {onlyAuthorized}, unbookableRoomIds) => {
    const unbookable = new Set(unbookableRoomIds);
    return _.fromPairs(
      Object.entries(activeBookings).map(([day, dayActiveBookings]) => {
        if (onlyAuthorized) {
          dayActiveBookings = dayActiveBookings.filter(
            ({reservation: {roomId}}) => !unbookable.has(roomId)
          );
        }
        const bookingsWithRooms = dayActiveBookings.map(dayActiveBooking => {
          const roomId = dayActiveBooking.reservation.roomId;
          const {reservation} = dayActiveBooking;
          return {...dayActiveBooking, reservation: {...reservation, room: allRooms[roomId]}};
        });
        return [day, bookingsWithRooms];
      })
    );
  }
);

export const getCalendarView = ({calendar}) => calendar.view;
