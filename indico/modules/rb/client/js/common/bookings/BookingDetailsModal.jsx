// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
      <Button
        {...props}
        icon="pencil"
        onClick={() => this.setState({mode: mode === 'edit' ? 'view' : 'edit'})}
        primary={mode === 'edit'}
        circular
      />
    );

    return isBeingEdited ? (
      <BookingEdit
        booking={booking}
        onClose={onClose}
        onSubmit={() => this.setState({mode: 'view'})}
        actionButtons={editButton}
      />
    ) : (
      <BookingDetails booking={booking} onClose={onClose} editButton={editButton} />
    );
  }
}

export default connect((state, {bookingId}) => ({
  booking: bookingsSelectors.getDetailsWithRoom(state, {bookingId}),
}))(BookingDetailsModal);
