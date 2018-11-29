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

import React from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Grid, Icon, Modal, Message} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {IndicoPropTypes} from 'indico/react/util';

import RoomBasicDetails from '../../components/RoomBasicDetails';
import BookingBootstrapForm from '../../components/BookingBootstrapForm';
import {selectors as roomsSelectors} from '../../common/rooms';
import * as bookRoomActions from './actions';
import * as bookRoomSelectors from './selectors';

import '../../common/rooms/RoomDetailsModal.module.scss';


function ConflictIndicator(
    {
        availability: {
            numDaysAvailable,
            allDaysAvailable
        }
    }
) {
    // todo: warning in case there are pre-booking conflicts
    return (
        allDaysAvailable ? (
            <Message color="green">
                <Icon name="check" />
                <Translate>The space will be free on the selected time slot(s)</Translate>
            </Message>
        ) : (
            numDaysAvailable ? (
                <Message color="yellow">
                    <Icon name="warning sign" />
                    <Translate>The space won't be available on one or more days</Translate>
                </Message>
            ) : (
                <Message color="red">
                    <Message.Header>
                        <Icon name="remove" />
                        <Translate>Space cannot be booked.</Translate>
                    </Message.Header>
                    <Translate>One or more bookings would conflict with yours.</Translate>
                </Message>
            )
        )
    );
}

ConflictIndicator.propTypes = {
    availability: PropTypes.object.isRequired
};

class BookFromListModal extends React.Component {
    static propTypes = {
        room: PropTypes.object.isRequired,
        refreshCollisions: PropTypes.func.isRequired,
        onClose: PropTypes.func,
        availability: PropTypes.object,
        availabilityLoading: PropTypes.bool.isRequired,
        defaults: PropTypes.object,
        actions: PropTypes.exact({
            resetCollisions: PropTypes.func.isRequired,
            openBookingForm: PropTypes.func.isRequired,
        }).isRequired,
        title: IndicoPropTypes.i18n
    };

    static defaultProps = {
        onClose: () => {},
        availability: null,
        defaults: undefined,
        title: <Translate>Book Room</Translate>
    };

    handleCloseModal = () => {
        const {onClose, actions: {resetCollisions}} = this.props;
        resetCollisions();
        onClose();
    };

    handleBook = (data) => {
        const {room, actions: {openBookingForm}} = this.props;
        openBookingForm(room.id, data);
    };

    render() {
        const {room, refreshCollisions, availability, availabilityLoading, defaults, title} = this.props;
        const buttonDisabled = availabilityLoading || !availability || availability.numDaysAvailable === 0;
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <Modal.Header styleName="room-details-header">
                    {title}
                </Modal.Header>
                <Modal.Content>
                    <Grid>
                        <Grid.Column width={8}>
                            <RoomBasicDetails room={room} />
                        </Grid.Column>
                        <Grid.Column width={8}>
                            <BookingBootstrapForm buttonCaption={<Translate>Book</Translate>}
                                                  buttonDisabled={buttonDisabled}
                                                  onChange={refreshCollisions}
                                                  onSearch={this.handleBook}
                                                  defaults={defaults}>
                                {availability && <ConflictIndicator availability={availability} />}
                            </BookingBootstrapForm>
                        </Grid.Column>
                    </Grid>
                </Modal.Content>
            </Modal>
        );
    }
}

export default connect(
    (state, {roomId}) => ({
        room: roomsSelectors.getRoom(state, {roomId}),
        availability: state.bookRoom.bookingForm.availability,
        availabilityLoading: bookRoomSelectors.isFetchingFormTimeline(state),
    }),
    (dispatch) => ({
        actions: bindActionCreators({
            resetCollisions: bookRoomActions.resetBookingAvailability,
            openBookingForm: bookRoomActions.openBookingForm,
        }, dispatch),
        dispatch,
    }),
    (stateProps, dispatchProps, ownProps) => {
        const {room} = stateProps;
        const {dispatch, ...realDispatchProps} = dispatchProps;
        return {
            ...ownProps,
            ...stateProps,
            ...realDispatchProps,
            refreshCollisions(filters) {
                dispatch(bookRoomActions.fetchBookingAvailability(room, filters));
            },
        };
    }
)(BookFromListModal);
