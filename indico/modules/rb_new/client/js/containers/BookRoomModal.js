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
import {connect} from 'react-redux';

import BookRoomModal from '../components/modals/BookRoomModal';
import {createBooking, fetchBookingAvailability} from '../actions';


const mapStateToProps = ({
    bookRoom: {filters: {recurrence, dates, timeSlot}},
    form: {roomModal},
    user
}, {room}) => {
    const bookingState = roomModal && roomModal.bookingState;
    const timeline = bookingState && bookingState.timeline;
    return {
        bookingData: {recurrence, dates, timeSlot, room},
        bookingState,
        user,
        availability: timeline && timeline.availability,
        dateRange: timeline && timeline.dateRange
    };
};

const mapDispatchToProps = (dispatch) => ({
    onSubmit: (
        {reason, usage, user, isPrebooking},
        __,
        {bookingData: {recurrence, dates, timeSlot, room: roomData}}) => {
        dispatch(createBooking({
            reason,
            usage,
            user,
            recurrence,
            dates,
            timeSlot,
            room: roomData,
            isPrebooking
        }));
    },
    dispatch
});

const mergeProps = (stateProps, dispatchProps, ownProps) => {
    const {bookingData: {room, ...filters}} = stateProps;
    const {dispatch} = dispatchProps;
    return {
        ...stateProps,
        ...dispatchProps,
        ...ownProps,
        fetchAvailability() {
            dispatch(fetchBookingAvailability(room, filters));
        }
    };
};

export default connect(
    mapStateToProps,
    mapDispatchToProps,
    mergeProps,
)(BookRoomModal);
