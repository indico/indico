// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import {connect} from 'react-redux';
import moment from 'moment';

import {toMoment} from 'indico/utils/date';
import * as bookRoomSelectors from './selectors';
import BookRoomModal from './BookRoomModal';
import BookFromListModal from './BookFromListModal';
import UnavailableRoomsModal from './UnavailableRoomsModal';
import {RoomDetailsPreloader} from '../../common/rooms';


const BookingDataProvider = connect(
    state => ({
        bookRoomFilters: bookRoomSelectors.getFilters(state),
    })
)(
    ({bookRoomFilters: {dates, timeSlot, recurrence}, bookingData: {isPrebooking}, ...restProps}) => (
        <BookRoomModal {...restProps} bookingData={{dates, timeSlot, recurrence, isPrebooking}} />
    )
);

const momentizeBookRoomDefaults = (defaults) => (!_.isEmpty(defaults) ? {
    ...defaults,
    dates: {
        startDate: toMoment(defaults.dates.startDate, moment.HTML5_FMT.DATE),
        endDate: toMoment(defaults.dates.endDate, moment.HTML5_FMT.DATE),
    },
    timeSlot: {
        startTime: toMoment(defaults.timeSlot.startTime, moment.HTML5_FMT.TIME),
        endTime: toMoment(defaults.timeSlot.endTime, moment.HTML5_FMT.TIME),
    },
} : undefined);


export default {
    /* eslint-disable react/display-name */
    'booking-form': (onClose, roomId, data) => {
        const {isPrebooking, ...bookingData} = data;
        return (
            <RoomDetailsPreloader roomId={roomId}>
                {() => (!_.isEmpty(bookingData)
                    ? <BookRoomModal roomId={roomId} onClose={onClose} bookingData={data} />
                    : <BookingDataProvider roomId={roomId} onClose={onClose} bookingData={data} />)}
            </RoomDetailsPreloader>
        );
    },
    'book-room': (onClose, roomId, data) => {
        const {isPrebooking, ...defaults} = data;
        return (
            <BookFromListModal roomId={roomId}
                               onClose={onClose}
                               defaults={momentizeBookRoomDefaults(defaults)}
                               isPrebooking={isPrebooking} />
        );
    },
    'unavailable-rooms': (onClose) => (
        <UnavailableRoomsModal onClose={onClose} />
    ),
};
