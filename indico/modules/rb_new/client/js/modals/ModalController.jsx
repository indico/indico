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

import qs from 'qs';
import React from 'react';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Dimmer, Loader} from 'semantic-ui-react';
import {push} from 'connected-react-router';

import {Preloader} from 'indico/react/util';
import {actions as roomsActions, selectors as roomsSelectors} from '../common/rooms';
import RoomDetailsModal from '../components/modals/RoomDetailsModal';
import BookFromListModal from '../components/modals/BookFromListModal';
import BookRoomModal from '../modules/bookRoom/BookRoomModal';
import * as globalSelectors from '../selectors';
import * as modalActions from './actions';
import {selectors as bookRoomSelectors} from '../modules/bookRoom';


class ModalController extends React.PureComponent {
    static propTypes = {
        isInitializing: PropTypes.bool.isRequired,
        path: PropTypes.string.isRequired,
        queryString: PropTypes.string.isRequired,
        bookRoomFilters: PropTypes.shape({
            dates: PropTypes.object.isRequired,
            timeSlot: PropTypes.object.isRequired,
            recurrence: PropTypes.object.isRequired,
        }).isRequired,
        actions: PropTypes.exact({
            pushState: PropTypes.func.isRequired,
            fetchRoomDetails: PropTypes.func.isRequired,
            openBookRoom: PropTypes.func.isRequired,
            openBookingForm: PropTypes.func.isRequired,
        }).isRequired,
    };

    getQueryData() {
        const {queryString} = this.props;
        let {modal: modalData} = qs.parse(queryString);
        if (!modalData) {
            return null;
        }
        if (Array.isArray(modalData)) {
            modalData = modalData[modalData.length - 1];
        }
        const match = modalData.match(/^([^:]+):([^:]+)(?::(.+))?$/); // foo:bar[:...]
        if (!match) {
            return null;
        }
        const [orig, name, value, payload] = match;
        return {orig, name, value, payload: JSON.parse(payload || 'null')};
    }

    getQueryStringWithout(arg) {
        const {queryString} = this.props;
        const params = qs.parse(queryString);
        if (Array.isArray(params.modal)) {
            params.modal = params.modal.filter(x => x !== arg);
        } else if (params.modal === arg) {
            delete params.modal;
        }
        return qs.stringify(params, {arrayFormat: 'repeat'});
    }

    makeCloseHandler(qsArg) {
        const {actions: {pushState}, path} = this.props;
        return () => {
            const queryString = this.getQueryStringWithout(qsArg);
            pushState(path + (queryString ? `?${queryString}` : ''));
        };
    }

    withRoomPreloader(name, roomId, render) {
        const {actions: {fetchRoomDetails}} = this.props;
        const key = `${name}-${roomId}`;
        return (
            <Preloader checkCached={state => roomsSelectors.hasDetails(state, {roomId})}
                       action={() => fetchRoomDetails(roomId)}
                       dimmer={<Dimmer active page><Loader /></Dimmer>}
                       key={key}>
                {render}
            </Preloader>
        );
    }

    renderRoomDetails(roomId, onClose, bookingPage = false) {
        const {actions: {openBookRoom, openBookingForm}, bookRoomFilters: {dates, timeSlot, recurrence}} = this.props;
        // if we are on the booking page, we have booking data in the redux state
        // and do not need to go through the bootstrap dialog
        const onBook = bookingPage
            ? (id) => openBookingForm(id, {dates, timeSlot, recurrence})
            : openBookRoom;
        return this.withRoomPreloader('roomDetails', roomId, () => (
            <RoomDetailsModal roomId={roomId} onClose={onClose} onBook={onBook} />
        ));
    }

    renderBookRoom(roomId, onClose) {
        return this.withRoomPreloader('bookRoom', roomId, () => (
            <BookFromListModal roomId={roomId} onClose={onClose} />
        ));
    }

    renderBookingForm(roomId, data, onClose) {
        return this.withRoomPreloader('bookingForm', roomId, () => (
            <BookRoomModal open roomId={roomId} onClose={onClose} bookingData={data} />
        ));
    }

    render() {
        const {isInitializing} = this.props;
        if (isInitializing) {
            return null;
        }
        const queryData = this.getQueryData();
        if (!queryData) {
            return null;
        }
        const {orig, name, value, payload} = queryData;
        const closeHandler = this.makeCloseHandler(orig);
        if (name === 'booking-form') {
            return this.renderBookingForm(value, payload, closeHandler);
        } else if (name === 'book-room') {
            return this.renderBookRoom(value, closeHandler);
        } else if (name === 'room-details') {
            return this.renderRoomDetails(value, closeHandler);
        } else if (name === 'room-details-book') {
            return this.renderRoomDetails(value, closeHandler, true);
        } else {
            return null;
        }
    }
}

export default connect(
    state => ({
        isInitializing: globalSelectors.isInitializing(state),
        bookRoomFilters: bookRoomSelectors.getFilters(state),
        path: state.router.location.pathname,
        queryString: state.router.location.search.substr(1),
    }),
    dispatch => ({
        actions: bindActionCreators({
            pushState: push,
            fetchRoomDetails: roomsActions.fetchDetails,
            openBookRoom: modalActions.openBookRoom,
            openBookingForm: modalActions.openBookingForm,
        }, dispatch),
    }),
)(ModalController);
