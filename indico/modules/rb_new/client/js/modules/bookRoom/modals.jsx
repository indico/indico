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
    ({bookRoomFilters: {dates, timeSlot, recurrence}, bookingData: {isPrebooking, link}, ...restProps}) => (
        <BookRoomModal {...restProps} bookingData={{dates, timeSlot, recurrence, isPrebooking, link}} />
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
        const {isPrebooking, link, ...bookingData} = data;
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
