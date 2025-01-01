// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import React from 'react';
import {connect} from 'react-redux';

import {toMoment} from 'indico/utils/date';

import {RoomDetailsPreloader} from '../../common/rooms';

import BookFromListModal from './BookFromListModal';
import BookRoomModal from './BookRoomModal';
import * as bookRoomSelectors from './selectors';
import UnavailableRoomsModal from './UnavailableRoomsModal';

const BookingDataProvider = connect(state => ({
  bookRoomFilters: bookRoomSelectors.getFilters(state),
}))(
  ({
    bookRoomFilters: {dates, timeSlot, recurrence, weekdays},
    bookingData: {isPrebooking},
    ...restProps
  }) => (
    <BookRoomModal
      {...restProps}
      bookingData={{dates, timeSlot, recurrence, weekdays, isPrebooking}}
    />
  )
);

const momentizeBookRoomDefaults = defaults =>
  !_.isEmpty(defaults)
    ? {
        ...defaults,
        dates: {
          startDate: toMoment(defaults.dates.startDate, moment.HTML5_FMT.DATE),
          endDate: toMoment(defaults.dates.endDate, moment.HTML5_FMT.DATE),
        },
        timeSlot: {
          startTime: toMoment(defaults.timeSlot.startTime, moment.HTML5_FMT.TIME),
          endTime: toMoment(defaults.timeSlot.endTime, moment.HTML5_FMT.TIME),
        },
      }
    : undefined;

export default {
  /* eslint-disable react/display-name */
  'booking-form': (onClose, roomId, data) => {
    const {isPrebooking, ...bookingData} = data;
    return (
      <RoomDetailsPreloader roomId={roomId}>
        {() =>
          !_.isEmpty(bookingData) ? (
            <BookRoomModal roomId={roomId} onClose={onClose} bookingData={data} />
          ) : (
            <BookingDataProvider roomId={roomId} onClose={onClose} bookingData={data} />
          )
        }
      </RoomDetailsPreloader>
    );
  },
  'book-room': (onClose, roomId, data) => {
    const {isPrebooking, ...defaults} = data;
    return (
      <BookFromListModal
        roomId={roomId}
        onClose={onClose}
        defaults={momentizeBookRoomDefaults(defaults)}
        isPrebooking={isPrebooking}
      />
    );
  },
  'unavailable-rooms': onClose => <UnavailableRoomsModal onClose={onClose} />,
};
