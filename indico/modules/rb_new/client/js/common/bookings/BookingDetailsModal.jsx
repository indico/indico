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
import {Button} from 'semantic-ui-react';
import BookingDetails from './BookingDetails';
import BookingEdit from './BookingEdit';
import * as bookingsSelectors from './selectors';


class BookingDetailsModal extends React.Component {
    static propTypes = {
        booking: PropTypes.object.isRequired,
        onClose: PropTypes.func,
    };

    static defaultProps = {
        onClose: () => {},
    };

    state = {
        mode: 'view',
    };

    render() {
        const {booking, onClose} = this.props;
        const {mode} = this.state;
        const isBeingEdited = mode === 'edit';
        const editButton = (props = {}) => (
            <Button {...props}
                    icon="pencil"
                    onClick={() => this.setState({mode: mode === 'edit' ? 'view' : 'edit'})}
                    primary={mode === 'edit'}
                    circular />
        );

        return isBeingEdited ? (
            <BookingEdit booking={booking}
                         onClose={onClose}
                         onSubmit={() => this.setState({mode: 'view'})}
                         actionButtons={editButton} />
        ) : (
            <BookingDetails booking={booking}
                            onClose={onClose}
                            actionButtons={editButton} />
        );
    }
}

export default connect(
    (state, {bookingId}) => ({
        booking: bookingsSelectors.getDetailsWithRoom(state, {bookingId}),
    }),
)(BookingDetailsModal);
