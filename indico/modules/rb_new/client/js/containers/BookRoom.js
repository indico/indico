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
import {goBack, push} from 'connected-react-router';

import BookRoom from '../components/pages/BookRoom';
import {
    fetchRooms,
    fetchMapRooms,
    setFilterParameter,
    updateRooms,
    fetchRoomDetails,
    resetBookingState
} from '../actions';


const mapStateToProps = ({bookRoom, roomDetails}) => ({...bookRoom, roomDetails});

const mapDispatchToProps = dispatch => ({
    clearRoomList() {
        dispatch(updateRooms('bookRoom', [], 0, true));
    },
    clearTextFilter() {
        dispatch(setFilterParameter('bookRoom', 'text', null));
    },
    fetchRooms(clear = true) {
        dispatch(fetchRooms('bookRoom', clear));
        dispatch(fetchMapRooms('bookRoom'));
    },
    fetchRoomDetails(id) {
        dispatch(fetchRoomDetails(id));
    },
    resetBookingState() {
        dispatch(resetBookingState());
    },
    setFilterParameter(param, value) {
        dispatch(setFilterParameter('bookRoom', param, value));
        dispatch(fetchRooms('bookRoom'));
        dispatch(fetchMapRooms('bookRoom'));
    },
    onModalClose() {
        dispatch(goBack());
    },
    pushState(url) {
        dispatch(push(url));
    }
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(BookRoom);
