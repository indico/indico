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
import {connect} from 'react-redux';
import PropTypes from 'prop-types';
import {Modal, Grid} from 'semantic-ui-react';
import {Translate} from 'indico/react/i18n';

import RoomBasicDetails from '../RoomBasicDetails';

import './BookingDetailsModal.module.scss';


class BookingDetailsModal extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
        onClose: PropTypes.func,
    };

    static defaultProps = {
        onClose: () => {}
    };

    handleCloseModal = () => {
        const {onClose} = this.props;
        onClose();
    };

    render() {
        const {booking} = this.props;
        return (
            <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
                <Modal.Header>
                    <Translate>Booking Details</Translate>
                </Modal.Header>
                <Modal.Content>
                    <BookingDetails booking={booking} />
                </Modal.Content>
            </Modal>
        );
    }
}

const mapStateToProps = () => {};

export default connect(
    mapStateToProps,
)(BookingDetailsModal);

BookingDetails.propTypes = {
    booking: PropTypes.object.isRequired
};

function BookingDetails({booking}) {
    const room = booking.room;
    return (
        <div>
            <Grid columns={2}>
                <Grid.Column>
                    <div>
                        <RoomBasicDetails room={room} />
                    </div>
                </Grid.Column>
                <Grid.Column>
                </Grid.Column>
            </Grid>
        </div>
    );
}
