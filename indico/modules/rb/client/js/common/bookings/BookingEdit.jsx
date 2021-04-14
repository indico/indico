// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import bookingEditTimelineURL from 'indico-url:rb.booking_edit_calendars';

import PropTypes from 'prop-types';
import React from 'react';
import {Form as FinalForm} from 'react-final-form';
import {connect} from 'react-redux';
import {bindActionCreators} from 'redux';
import {Button, Checkbox, Grid, Icon, Message, Modal, Segment} from 'semantic-ui-react';

import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import {serializeDate, serializeTime} from 'indico/utils/date';

import RoomBasicDetails from '../../components/RoomBasicDetails';
import {getRecurrenceInfo, preProcessParameters, serializeRecurrenceInfo} from '../../util';
import {ajax as ajaxFilterRules} from '../roomSearch/serializers';
import {selectors as userSelectors} from '../user';

import * as bookingsActions from './actions';
import BookingEditCalendar from './BookingEditCalendar';
import BookingEditForm from './BookingEditForm';
import * as bookingsSelectors from './selectors';

import './BookingEdit.module.scss';

function validate({reason}) {
  const errors = {};
  if (reason && reason.length < 3) {
    errors.reason = Translate.string('Reason must be at least 3 characters');
  }
  return errors;
}

const INITIAL_CALENDAR_DATA = {
  currentBooking: {
    dateRange: [],
    data: {},
  },
};

class BookingEdit extends React.Component {
  static propTypes = {
    user: PropTypes.object.isRequired,
    booking: PropTypes.object.isRequired,
    isOngoingBooking: PropTypes.bool.isRequired,
    actionButtons: PropTypes.func,
    onSubmit: PropTypes.func.isRequired,
    onClose: PropTypes.func,
    actions: PropTypes.exact({
      updateBooking: PropTypes.func.isRequired,
    }).isRequired,
  };

  static defaultProps = {
    actionButtons: () => {},
    onClose: () => {},
  };

  constructor(props) {
    super(props);

    this.state = {
      skipConflicts: false,
      numberOfConflicts: null,
      numberOfCandidates: null,
      willBookingSplit: false,
      calendars: null,
    };
  }

  async componentDidMount() {
    // we need to use setState here to rerender the
    // eslint-disable-next-line react/no-did-mount-set-state
    this.setState({calendars: INITIAL_CALENDAR_DATA});

    const {dates, timeSlot, recurrence} = this.initialFormValues;
    const {
      calendars: [currentBooking],
    } = await this.fetchBookingTimelineInfo({dates, timeSlot, recurrence});

    // eslint-disable-next-line react/no-did-mount-set-state
    this.setState({
      isLoading: false,
      calendars: {
        currentBooking,
      },
    });
  }

  get initialFormValues() {
    const {
      user: sessionUser,
      booking: {repetition, startDt, endDt, bookedForUser, bookingReason},
    } = this.props;
    const recurrence = getRecurrenceInfo(repetition);
    const isSingleBooking = recurrence.type === 'single';
    const dates = {
      startDate: serializeDate(startDt),
      endDate: isSingleBooking ? null : serializeDate(endDt),
    };
    const timeSlot = {startTime: serializeTime(startDt), endTime: serializeTime(endDt)};
    const usage = bookedForUser.id === sessionUser.id ? 'myself' : 'someone';

    return {
      recurrence,
      dates,
      timeSlot,
      usage,
      user: bookedForUser.identifier,
      reason: bookingReason,
    };
  }

  fetchBookingTimelineInfo = async bookingDTInfo => {
    const {dates, timeSlot, recurrence} = bookingDTInfo;
    const {
      booking: {id},
    } = this.props;
    const params = preProcessParameters({timeSlot, recurrence, dates}, ajaxFilterRules);

    let response;
    try {
      response = await indicoAxios.get(bookingEditTimelineURL({booking_id: id}), {params});
    } catch (error) {
      handleAxiosError(error);
      return;
    }

    return camelizeKeys(response.data);
  };

  updateBookingCalendar = async (dates, timeSlot, recurrence) => {
    this.setState({
      numberOfCandidates: null,
      numberOfConflicts: null,
      skipConflicts: false,
      calendars: INITIAL_CALENDAR_DATA,
      isLoading: true,
      willBookingSplit: false,
    });

    const {calendars, willBeSplit} = await this.fetchBookingTimelineInfo({
      dates,
      timeSlot,
      recurrence,
    });
    const [currentBooking, newBooking] = calendars;

    this.setState({
      numberOfCandidates: newBooking ? newBooking.data.numDaysAvailable : null,
      numberOfConflicts: newBooking ? newBooking.data.numConflicts : null,
      isLoading: false,
      willBookingSplit: willBeSplit,
      calendars: {
        currentBooking,
        newBooking,
      },
    });
  };

  renderBookingEditModal = fprops => {
    const {submitting, submitSucceeded, hasValidationErrors, pristine} = fprops;
    const {booking, onClose, actionButtons, isOngoingBooking} = this.props;
    const {room} = booking;
    const {
      skipConflicts,
      willBookingSplit,
      calendars,
      numberOfConflicts,
      numberOfCandidates,
      isLoading,
    } = this.state;
    const conflictingBooking = numberOfConflicts > 0 && !skipConflicts;
    const submitBlocked =
      submitting || submitSucceeded || hasValidationErrors || pristine || conflictingBooking;

    return (
      <Modal size="large" onClose={onClose} closeIcon open>
        <Modal.Header styleName="booking-edit-modal-header">
          <Translate>Edit a booking</Translate>
          {actionButtons()}
        </Modal.Header>
        <Modal.Content>
          <Grid stackable columns={2}>
            <Grid.Column>
              <RoomBasicDetails room={room} />
              {isOngoingBooking && (
                <Message color="blue" styleName="ongoing-booking-info" icon>
                  <Icon name="play" />
                  <Translate>This booking has already started.</Translate>
                </Message>
              )}
              <BookingEditForm
                booking={booking}
                formProps={fprops}
                onBookingPeriodChange={this.updateBookingCalendar}
              />
            </Grid.Column>
            <Grid.Column stretched>
              {!!calendars && (
                <BookingEditCalendar
                  calendars={calendars}
                  booking={booking}
                  numberOfCandidates={numberOfCandidates}
                  numberOfConflicts={numberOfConflicts}
                  willBookingSplit={willBookingSplit}
                  isLoading={isLoading}
                />
              )}
              {this.renderConflictsMessage()}
            </Grid.Column>
          </Grid>
        </Modal.Content>
        <Modal.Actions>
          <Button
            type="submit"
            form="booking-edit-form"
            disabled={submitBlocked || isLoading}
            primary
          >
            <Translate>Save changes</Translate>
          </Button>
          <Button type="button" onClick={onClose}>
            <Translate>Close</Translate>
          </Button>
        </Modal.Actions>
      </Modal>
    );
  };

  renderConflictsMessage = () => {
    const {skipConflicts, numberOfConflicts, numberOfCandidates} = this.state;

    if (!numberOfConflicts) {
      return null;
    }

    return (
      <div styleName="booking-conflicts-info">
        <Message color="yellow" attached icon>
          <Icon name="warning circle" />
          <Message.Content>
            <Message.Header>
              <Translate>Conflicts with new booking</Translate>
            </Message.Header>
            <PluralTranslate count={numberOfConflicts}>
              <Singular>Your new booking conflicts with another one.</Singular>
              <Plural>
                <Param name="count" value={numberOfConflicts} /> occurrences of your booking are
                unavailable due to conflicts.
              </Plural>
            </PluralTranslate>
          </Message.Content>
        </Message>
        {numberOfCandidates > 0 && numberOfConflicts > 0 && (
          <Segment attached="bottom">
            <Checkbox
              toggle
              defaultChecked={skipConflicts}
              label={Translate.string(
                'I understand, please skip any days with conflicting ' + 'occurrences.'
              )}
              onChange={(__, {checked}) => {
                this.setState({
                  skipConflicts: checked,
                });
              }}
            />
          </Segment>
        )}
      </div>
    );
  };

  updateBooking = async data => {
    const {
      dates: {startDate, endDate},
      timeSlot: {startTime, endTime},
      user,
      reason,
      recurrence,
    } = data;
    const {
      actions: {updateBooking},
      booking: {
        id,
        room: {id: roomId},
      },
      onSubmit,
    } = this.props;
    const [repeatFrequency, repeatInterval] = serializeRecurrenceInfo(recurrence);
    const params = {
      start_dt: `${startDate} ${startTime}`,
      end_dt: `${endDate ? endDate : startDate} ${endTime}`,
      repeat_frequency: repeatFrequency,
      repeat_interval: repeatInterval,
      room_id: roomId,
      user,
      reason,
    };

    const rv = await updateBooking(id, params);
    if (rv.error) {
      return rv.error;
    } else {
      onSubmit();
    }
  };

  render() {
    return (
      <FinalForm
        onSubmit={this.updateBooking}
        render={this.renderBookingEditModal}
        initialValues={this.initialFormValues}
        subscription={{
          submitting: true,
          submitSucceeded: true,
          hasValidationErrors: true,
          pristine: true,
          values: true,
        }}
        validate={validate}
        keepDirtyOnReinitialize
      />
    );
  }
}

export default connect(
  (state, {booking: {id}}) => ({
    user: userSelectors.getUserInfo(state),
    isOngoingBooking: bookingsSelectors.isOngoingBooking(state, {bookingId: id}),
  }),
  dispatch => ({
    actions: bindActionCreators(
      {
        updateBooking: bookingsActions.updateBooking,
      },
      dispatch
    ),
  })
)(BookingEdit);
