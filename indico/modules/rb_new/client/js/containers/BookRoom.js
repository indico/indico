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

import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {stateToQueryString} from 'redux-router-querystring';

import {queryString as queryStringFilterSerializer} from '../serializers/filters';
import {queryString as queryStringTimelineSerializer} from '../serializers/timeline';
import BookRoom from '../components/pages/BookRoom';
import {
    fetchRooms,
    fetchMapRooms,
    setFilterParameter,
    updateRooms,
    resetBookingState,
    toggleTimelineView
} from '../actions';
import {pushStateMergeProps} from '../util';
import {actions as roomsActions, selectors as roomsSelectors} from '../common/rooms';


const mapStateToProps = (state) => {
    return {
        ...state.bookRoom,
        roomDetailsFetching: roomsSelectors.isFetching(state),
        queryString: stateToQueryString(state.bookRoom, queryStringFilterSerializer, queryStringTimelineSerializer),
        showMap: !!state.mapAspects.list && !!state.staticData.tileServerURL,
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
    fetchRoomDetails: bindActionCreators(roomsActions.fetchDetails, dispatch),
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
