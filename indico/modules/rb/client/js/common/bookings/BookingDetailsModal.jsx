// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {connect} from 'react-redux';
import {Button} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import BookingDetails from './BookingDetails';
import BookingEdit from './BookingEdit';
import * as bookingsSelectors from './selectors';

import './BookingDetailsModal.module.scss';

class BookingDetailsModal extends React.Component {
  static propTypes = {
    booking: PropTypes.object.isRequired,
    onClose: PropTypes.func,
    cancelDate: PropTypes.string,
  };

  static defaultProps = {
    onClose: () => {},
    cancelDate: null,
  };

  state = {
    mode: 'view',
  };

  componentWillUnmount() {
    if (this.previousFocus?.isConnected && this.previousFocus !== document.body) {
      this.previousFocus.focus();
    }
  }

  previousFocus = document.activeElement;

  render() {
    const {booking, onClose, cancelDate} = this.props;
    const {mode} = this.state;
    const isBeingEdited = mode === 'edit';
    const editButton = (props = {}) => (
      <Button
        {...props}
        icon="pencil"
        onClick={() => this.setState({mode: mode === 'edit' ? 'view' : 'edit'})}
        primary={mode === 'edit'}
        circular
        content={
          <span styleName="visually-hidden">
            {mode === 'edit' ? (
              <Translate>Return to booking details</Translate>
            ) : (
              <Translate>Edit booking</Translate>
            )}
          </span>
        }
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
      <BookingDetails
        booking={booking}
        onClose={onClose}
        editButton={editButton}
        cancelDate={cancelDate}
      />
    );
  }
}

export default connect((state, {bookingId}) => ({
  booking: bookingsSelectors.getDetailsWithRoom(state, {bookingId}),
}))(BookingDetailsModal);
