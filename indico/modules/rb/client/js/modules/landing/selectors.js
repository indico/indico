// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {selectors as roomSelectors} from '../../common/rooms';

export const getStatistics = ({landing}) => landing.stats.data;
export const hasStatistics = state => getStatistics(state) !== null;
export const hasUpcomingBookings = ({
  landing: {
    upcomingBookings: {data},
  },
}) => !!(data && data.length);
export const hasFetchedUpcomingBookings = ({
  landing: {
    upcomingBookings: {request},
  },
}) => request.state === 'success';
export const getUpcomingBookings = createSelector(
  ({landing}) => landing.upcomingBookings.data,
  roomSelectors.getAllRooms,
  (upcomingBookings, rooms) => {
    return upcomingBookings.map(upcomingBooking => {
      const {reservation} = upcomingBooking;
      return {...upcomingBooking, reservation: {...reservation, room: rooms[reservation.roomId]}};
    });
  }
);
