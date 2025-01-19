// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import Overridable from 'react-overridable';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Grid, Icon, Modal, Message} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {IndicoPropTypes} from 'indico/react/util';
import {createDT, isBookingStartDTValid} from 'indico/utils/date';

import {selectors as configSelectors} from '../../common/config';
import {selectors as roomsSelectors} from '../../common/rooms';
import {selectors as userSelectors} from '../../common/user';
import BookingBootstrapForm from '../../components/BookingBootstrapForm';
import RoomBasicDetails from '../../components/RoomBasicDetails';

import * as bookRoomActions from './actions';
import * as bookRoomSelectors from './selectors';

import '../../common/rooms/RoomDetailsModal.module.scss';

function ConflictIndicator({availability: {numDaysAvailable, allDaysAvailable}}) {
  // todo: warning in case there are pre-booking conflicts
  return allDaysAvailable ? (
    <Message color="green">
      <Icon name="check" />
      <Translate>The space will be free on the selected time slot(s)</Translate>
    </Message>
  ) : numDaysAvailable ? (
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
  );
}

ConflictIndicator.propTypes = {
  availability: PropTypes.object.isRequired,
};

class BookFromListModal extends React.Component {
  static propTypes = {
    room: PropTypes.object.isRequired,
    refreshCollisions: PropTypes.func.isRequired,
    onClose: PropTypes.func,
    availability: PropTypes.object,
    availabilityLoading: PropTypes.bool.isRequired,
    isAdminOverrideEnabled: PropTypes.bool.isRequired,
    defaults: PropTypes.object,
    actions: PropTypes.exact({
      resetCollisions: PropTypes.func.isRequired,
      openBookingForm: PropTypes.func.isRequired,
    }).isRequired,
    isPrebooking: PropTypes.bool,
    labels: PropTypes.shape({
      bookTitle: IndicoPropTypes.i18n,
      preBookTitle: IndicoPropTypes.i18n,
      bookBtn: IndicoPropTypes.i18n,
      preBookBtn: IndicoPropTypes.i18n,
    }),
    bookingGracePeriod: PropTypes.number,
  };

  static defaultProps = {
    onClose: () => {},
    availability: null,
    defaults: undefined,
    isPrebooking: false,
    labels: {
      bookTitle: <Translate>Book Room</Translate>,
      preBookTitle: <Translate>Pre-Book Room</Translate>,
      bookBtn: <Translate>Book</Translate>,
      preBookBtn: <Translate>Pre-Book</Translate>,
    },
    bookingGracePeriod: null,
  };

  state = {
    pastDTChosen: false,
  };

  handleCloseModal = () => {
    const {
      onClose,
      actions: {resetCollisions},
    } = this.props;
    resetCollisions();
    onClose();
  };

  handleBook = data => {
    const {
      room,
      actions: {openBookingForm},
      isPrebooking,
    } = this.props;
    openBookingForm(room.id, {...data, isPrebooking});
  };

  onFiltersChange = filters => {
    const {refreshCollisions, isAdminOverrideEnabled, bookingGracePeriod} = this.props;
    const {
      dates: {startDate},
      timeSlot,
    } = filters;

    refreshCollisions(filters);
    if (!startDate) {
      this.setState({pastDTChosen: true});
      return;
    }

    const startTime = timeSlot && timeSlot.startTime ? timeSlot.startTime : '00:00';
    const startDt = createDT(startDate, startTime);
    this.setState({
      pastDTChosen: !isBookingStartDTValid(startDt, isAdminOverrideEnabled, bookingGracePeriod),
    });
  };

  render() {
    const {
      room,
      availability,
      availabilityLoading,
      defaults,
      isPrebooking,
      labels,
      isAdminOverrideEnabled,
    } = this.props;
    const {pastDTChosen} = this.state;
    const buttonDisabled =
      availabilityLoading || !availability || availability.numDaysAvailable === 0;
    return (
      <Modal open onClose={this.handleCloseModal} size="large" closeIcon>
        <Modal.Header styleName="room-details-header">
          {isPrebooking ? labels.preBookTitle : labels.bookTitle}
        </Modal.Header>
        <Modal.Content>
          <Grid stackable>
            <Grid.Column width={8}>
              <RoomBasicDetails room={room} />
            </Grid.Column>
            <Grid.Column width={8}>
              <BookingBootstrapForm
                buttonCaption={isPrebooking ? labels.preBookBtn : labels.bookBtn}
                buttonDisabled={buttonDisabled}
                onChange={this.onFiltersChange}
                onSearch={this.handleBook}
                defaults={defaults}
              >
                {availability && <ConflictIndicator availability={availability} />}
                {pastDTChosen && !isAdminOverrideEnabled && (
                  <Message color="red">
                    <Icon name="dont" />
                    <Translate>Bookings in the past are not allowed.</Translate>
                  </Message>
                )}
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
    isAdminOverrideEnabled: userSelectors.isUserAdminOverrideEnabled(state),
    bookingGracePeriod: configSelectors.getBookingGracePeriod(state),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        resetCollisions: bookRoomActions.resetBookingAvailability,
        openBookingForm: bookRoomActions.openBookingForm,
      },
      dispatch
    ),
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
)(Overridable.component('BookFromListModal', BookFromListModal));
