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
import {stateToQueryString} from 'redux-router-querystring';

import {queryString as queryStringSerializer} from '../serializers/filters';
import BookRoom from '../components/pages/BookRoom';
import {
    fetchRooms,
    fetchMapRooms,
    setFilterParameter,
    updateRooms,
    fetchRoomDetails,
    resetBookingState,
    toggleTimelineView
} from '../actions';
import {pushStateMergeProps} from '../util';


const mapStateToProps = ({bookRoom, mapAspects: {list}, roomDetails, staticData: {tileServerURL}}) => {
    return {
        ...bookRoom,
        roomDetails,
        queryString: stateToQueryString(bookRoom, queryStringSerializer),
        showMap: !!list.length && !!tileServerURL
    };
};

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
    toggleTimelineView: (isVisible) => {
        dispatch(toggleTimelineView(isVisible));
    },
    dispatch
});

export default connect(
    mapStateToProps,
    mapDispatchToProps,
    pushStateMergeProps
)(BookRoom);
