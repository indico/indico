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
import {connect} from 'react-redux';
import {stateToQueryString} from 'redux-router-querystring';
import {Grid, Icon, Modal, Message} from 'semantic-ui-react';
import {push} from 'connected-react-router';

import {Translate} from 'indico/react/i18n';

import './RoomDetailsModal.module.scss';
import {queryString as queryStringSerializer} from '../../serializers/filters';
import {RoomBasicDetails} from '../RoomBasicDetails';
import {setFilters, fetchBookingAvailability, resetBookingState} from '../../actions';
import BookingBootstrapForm from '../BookingBootstrapForm';


function ConflictIndicator(
    {
        availability: {
            num_days_available: numDaysAvailable,
            all_days_available: allDaysAvailable
        }
    }
) {
    // todo: warning in case there are pre-booking conflicts
    return (
        allDaysAvailable ? (
            <Message color="green">
                <Icon name="check" />
                <Translate>The room will be free on the selected time slot(s)</Translate>
            </Message>
        ) : (
            numDaysAvailable ? (
                <Message color="yellow">
                    <Icon name="warning sign" />
                    <Translate>The room won't be available on one or more days</Translate>
                </Message>
            ) : (
                <Message color="red">
                    <Message.Header>
                        <Icon name="remove" />
                        <Translate>Room cannot be booked.</Translate>
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
        resetCollisions: PropTypes.func.isRequired,
        onClose: PropTypes.func,
        onBook: PropTypes.func.isRequired,
        availability: PropTypes.object
    };

    static defaultProps = {
        onClose: () => {},
        availability: null
    };

    handleCloseModal = () => {
        const {onClose, resetCollisions} = this.props;
        resetCollisions();
        onClose();
    };

    render() {
        const {room, refreshCollisions, availability, onBook} = this.props;
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <Modal.Header styleName="room-details-header">
                    <Translate>Book Room</Translate>
                </Modal.Header>
                <Modal.Content>
                    <Grid>
                        <Grid.Column width={8}>
                            <RoomBasicDetails room={room} />
                        </Grid.Column>
                        <Grid.Column width={8}>
                            <BookingBootstrapForm buttonCaption={<Translate>Book</Translate>}
                                                  buttonDisabled={availability && availability.num_days_available === 0}
                                                  onChange={refreshCollisions}
                                                  onSearch={onBook}>
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
    ({bookRoomForm: {timeline}}) => ({
        availability: timeline ? timeline.availability : null
    }),
    (dispatch, {room}) => ({
        refreshCollisions(filters) {
            dispatch(fetchBookingAvailability(room, filters));
        },
        resetCollisions() {
            dispatch(resetBookingState());
        },
        onBook(filters) {
            const qs = stateToQueryString({filters}, queryStringSerializer);
            dispatch(setFilters('bookRoom', filters));
            dispatch(push(`/book/${room.id}/confirm?${qs}`));
        }
    })
)(BookFromListModal);
