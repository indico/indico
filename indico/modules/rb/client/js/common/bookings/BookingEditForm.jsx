// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Field, FormSpy} from 'react-final-form';
import Overridable from 'react-overridable';
import {connect} from 'react-redux';
import {Form, Message, Segment, Icon} from 'semantic-ui-react';

import {FinalPrincipal, FinalDatePicker, FinalDateRangePicker} from 'indico/react/components';
import {
  FieldCondition,
  FinalDropdown,
  FinalInput,
  FinalRadio,
  FinalTextArea,
  parsers as p,
  validators as v,
} from 'indico/react/forms';
import {FavoritesProvider} from 'indico/react/hooks';
import {PluralTranslate, Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';
import {renderPluginComponents} from 'indico/utils/plugins';

import {selectors as configSelectors} from '../../common/config';
import {FinalTimeRangePicker} from '../../components/TimeRangePicker';
import {FinalWeekdayRecurrencePicker} from '../../components/WeekdayRecurrencePicker';
import {sanitizeRecurrence, getRecurrenceInfo} from '../../util';
import {selectors as userSelectors} from '../user';

import './BookingEditForm.module.scss';

class BookingEditForm extends React.Component {
  static propTypes = {
    user: PropTypes.object.isRequired,
    booking: PropTypes.object.isRequired,
    formProps: PropTypes.object.isRequired,
    onBookingPeriodChange: PropTypes.func,
    onExtraFieldsChange: PropTypes.func,
    hideOptions: PropTypes.objectOf(PropTypes.bool),
    bookingReasonRequired: PropTypes.string.isRequired,
  };

  static defaultProps = {
    onBookingPeriodChange: () => {},
    hideOptions: {},
    onExtraFieldsChange: () => null,
  };

  showApprovalWarning = (dirtyFields, initialValues, values) => {
    const initialStartTime = moment(initialValues.timeSlot.startTime, 'HH:mm');
    const initialEndTime = moment(initialValues.timeSlot.endTime, 'HH:mm');
    const newStartTime = moment(values.timeSlot.startTime, 'HH:mm');
    const newEndTime = moment(values.timeSlot.endTime, 'HH:mm');
    return (
      Object.keys(dirtyFields).some(key => key === 'dates' || key.startsWith('recurrence.')) ||
      newStartTime.isBefore(initialStartTime) ||
      newEndTime.isAfter(initialEndTime)
    );
  };

  recurrenceTypeChanged = newType => {
    const {
      booking: {startDt},
      onBookingPeriodChange,
      formProps: {
        form,
        values: {recurrence, dates, timeSlot},
      },
    } = this.props;
    const filters = {dates, recurrence: {...recurrence, type: newType}};
    const today = moment();

    if (['daily', 'every'].includes(newType) && today.isAfter(startDt, 'day')) {
      dates.startDate = serializeDate(startDt);
    } else if (newType === 'single') {
      if (today.isAfter(startDt, 'minute')) {
        dates.startDate = serializeDate(today.add(1, 'day'));
      } else {
        dates.startDate = serializeDate(startDt);
      }
    }

    sanitizeRecurrence(filters);
    form.change('recurrence', filters.recurrence);
    form.change('dates', filters.dates);

    onBookingPeriodChange(filters.dates, timeSlot, filters.recurrence);

    if (newType === 'every' && recurrence.interval === 'week') {
      this.preselectWeekdayToday(form, true);
    } else {
      form.change('recurrence.weekdays', []);
    }
  };

  clearWeekdays = interval => {
    const {
      formProps: {
        values: {recurrence},
      },
    } = this.props;
    const updatedWeekdays = interval === 'month' ? [] : recurrence.weekdays;
    return {...recurrence, weekdays: updatedWeekdays};
  };

  getMinDate = () => {
    // XXX why don't we support admin override here?
    return serializeDate(moment());
  };

  preselectWeekdayToday = (form, force = false) => {
    const {
      formProps: {
        values: {recurrence},
      },
    } = this.props;

    const today = moment().locale('en').format('ddd').toLowerCase();

    if (
      ((recurrence.type === 'every' && recurrence.interval === 'week') || force) &&
      (recurrence.weekdays === null || recurrence.weekdays.length === 0)
    ) {
      const newRecurrence = {...recurrence, weekdays: [today]};
      form.change('recurrence.weekdays', newRecurrence.weekdays);
    }
  };

  getRecurrenceLabel = number => {
    const {hideOptions} = this.props;

    if (hideOptions.recurringWeekly && hideOptions.recurringMonthly) {
      return null;
    }

    if (hideOptions.recurringWeekly) {
      return [{text: PluralTranslate.string('Month', 'Months', number || 0), value: 'month'}];
    }

    if (hideOptions.recurringMonthly) {
      return [{text: PluralTranslate.string('Week', 'Weeks', number || 0), value: 'week'}];
    }
  };

  render() {
    const {
      user: sessionUser,
      booking,
      onBookingPeriodChange,
      formProps,
      hideOptions,
      bookingReasonRequired,
      onExtraFieldsChange,
    } = this.props;
    const {bookedForUser, startDt, endDt, room, isAccepted, repetition, link} = booking;
    const {
      values: {dates, recurrence, timeSlot, usage},
      submitSucceeded,
      submitting,
      form,
      handleSubmit,
    } = formProps;
    const requireReason =
      {always: true, never: false, not_for_events: !link}[bookingReasonRequired] ?? true;
    const bookedByCurrentUser = sessionUser.id === bookedForUser.id;
    const today = moment();
    const bookingStarted = today.isAfter(startDt, 'day');
    const bookingFinished = today.isAfter(endDt, 'day');
    const recurringBookingInProgress = getRecurrenceInfo(repetition).type === 'every';
    const recurrenceHidden = hideOptions.recurringWeekly && hideOptions.recurringMonthly;

    // all but one option are hidden
    const showRecurrenceOptions =
      ['single', 'daily', 'recurring'].filter(x => hideOptions[x]).length !== 2;
    const hideMessage = hideOptions.recurringWeekly || hideOptions.recurringMonthly;
    return (
      <Form id="booking-edit-form" styleName="booking-edit-form" onSubmit={handleSubmit}>
        {!hideMessage && recurringBookingInProgress && recurrence.type === 'every' && (
          <Message icon styleName="repeat-frequency-disabled-notice">
            <Icon name="dont" />
            <Translate>You cannot modify the repeat frequency of an existing booking.</Translate>
          </Message>
        )}
        <Segment>
          {showRecurrenceOptions && (
            <Form.Group inline>
              {!hideOptions.single && (
                <FinalRadio
                  name="recurrence.type"
                  label={Translate.string('Single booking')}
                  value="single"
                  disabled={submitSucceeded || bookingFinished}
                  onClick={() => this.recurrenceTypeChanged('single')}
                />
              )}
              {!hideOptions.daily && (
                <FinalRadio
                  name="recurrence.type"
                  label={Translate.string('Daily booking')}
                  value="daily"
                  disabled={submitSucceeded || bookingFinished}
                  onClick={() => this.recurrenceTypeChanged('daily')}
                />
              )}
              {!recurrenceHidden && (
                <FinalRadio
                  name="recurrence.type"
                  label={Translate.string('Recurring booking')}
                  value="every"
                  disabled={submitSucceeded || bookingFinished}
                  onClick={() => this.recurrenceTypeChanged('every')}
                />
              )}
            </Form.Group>
          )}
          {recurrence.type === 'every' && (
            <Form.Group inline>
              <label>
                <Translate>Every</Translate>
              </label>
              <FinalInput
                name="recurrence.number"
                type="number"
                min="1"
                max="99"
                step="1"
                validate={v.min(1)}
                disabled={submitSucceeded}
                required
                parse={p.number}
                onChange={newNumber => {
                  if (newNumber > 0) {
                    const newRecurrence = {...recurrence, number: newNumber};
                    onBookingPeriodChange(dates, timeSlot, newRecurrence);
                  }
                }}
              />
              {hideOptions.recurringWeekly || hideOptions.recurringMonthly ? (
                <label>{this.getRecurrenceLabel(recurrence.number).map(x => x.text)}</label>
              ) : (
                <Field name="recurrence.number" subscription={{}}>
                  {({input: {value: number}}) => (
                    <FinalDropdown
                      name="recurrence.interval"
                      disabled={submitSucceeded || recurringBookingInProgress}
                      selection
                      required
                      options={[
                        {
                          value: 'week',
                          text: PluralTranslate.string('Week', 'Weeks', number || 0),
                        },
                        {
                          value: 'month',
                          text: PluralTranslate.string('Month', 'Months', number || 0),
                        },
                      ]}
                      onChange={newInterval => {
                        onBookingPeriodChange(dates, timeSlot, this.clearWeekdays(newInterval));
                        this.preselectWeekdayToday(form);
                      }}
                    />
                  )}
                </Field>
              )}
            </Form.Group>
          )}
          {recurrence.type === 'single' ? (
            <FinalDatePicker
              name="dates"
              asRange
              onChange={newDates => {
                if (newDates.startDate !== '__invalid__') {
                  onBookingPeriodChange(newDates, timeSlot, recurrence);
                }
              }}
              disabled={submitSucceeded || bookingFinished}
              min={this.getMinDate()}
            />
          ) : (
            <FinalDateRangePicker
              name="dates"
              onChange={newDates => {
                onBookingPeriodChange(newDates, timeSlot, this.clearWeekdays(recurrence.interval));
              }}
              disabled={submitSucceeded || bookingFinished}
              startDisabled={bookingStarted}
              min={this.getMinDate()}
            />
          )}
          {!hideOptions.timeSlot && (
            <FinalTimeRangePicker
              name="timeSlot"
              onChange={newTimeSlot => {
                onBookingPeriodChange(dates, newTimeSlot, recurrence);
              }}
              allowPastTimes
              disabled={submitSucceeded || bookingFinished}
            />
          )}
          <div
            style={
              recurrence.type === 'every' && recurrence.interval === 'week' ? {} : {display: 'none'}
            }
          >
            <div styleName="recurring-every-label">
              <Translate>Recurring every</Translate>
            </div>
            <FinalWeekdayRecurrencePicker
              name="recurrence.weekdays"
              requireOneSelected
              onChange={newWeekdays => {
                const newRecurrence = {...recurrence, weekdays: newWeekdays};
                onBookingPeriodChange(dates, timeSlot, newRecurrence);
              }}
            />
          </div>
          {!room.canUserBook && room.canUserPrebook && isAccepted && (
            <FormSpy subscription={{dirtyFields: true, initialValues: true, values: true}}>
              {({dirtyFields, initialValues, values}) =>
                this.showApprovalWarning(dirtyFields, initialValues, values) && (
                  <Message warning visible>
                    <Message.Header>
                      <Translate>This booking will require approval!</Translate>
                    </Message.Header>
                    <Translate>
                      Changing date or time will revert it back to a pre-booking.
                    </Translate>
                  </Message>
                )
              }
            </FormSpy>
          )}
        </Segment>
        <Segment color="blue" inverted>
          <Form.Group>
            <FinalRadio
              name="usage"
              value="myself"
              onClick={() => form.change('user', sessionUser.identifier)}
              label={Translate.string("I'll be using it myself")}
              disabled={submitSucceeded}
              checked={usage === 'myself'}
            />
            <FinalRadio
              name="usage"
              value="someone"
              onClick={() =>
                form.change('user', bookedByCurrentUser ? null : bookedForUser.identifier)
              }
              label={Translate.string("I'm booking it for someone else")}
              disabled={submitSucceeded}
              checked={usage === 'someone'}
            />
          </Form.Group>
          <FieldCondition when="usage" is="someone">
            <FavoritesProvider>
              {favoriteUsersController => (
                <FinalPrincipal
                  name="user"
                  favoriteUsersController={favoriteUsersController}
                  disabled={submitSucceeded}
                  withExternalUsers
                  required
                />
              )}
            </FavoritesProvider>
          </FieldCondition>
          <FinalTextArea
            name="reason"
            nullIfEmpty
            placeholder={Translate.string('Reason for booking')}
            required={requireReason}
            disabled={submitSucceeded}
          />
        </Segment>
        {renderPluginComponents('rb-booking-form-extra-fields', {
          room,
          booking,
          disabled: submitSucceeded || submitting,
          onSubmit: item => onExtraFieldsChange(item),
        })}

        {room.canUserViewInternalNotes && (
          <Segment inverted styleName="internal-notes-segment">
            <p style={{marginBottom: '0.5em'}}>
              <Translate>
                Internal notes about the booking are only visible to room managers.
              </Translate>
            </p>
            <FinalTextArea name="internalNote" disabled={submitSucceeded} />
          </Segment>
        )}
      </Form>
    );
  }
}

export default connect(state => ({
  user: userSelectors.getUserInfo(state),
  bookingReasonRequired: configSelectors.getBookingReasonRequired(state),
}))(Overridable.component('BookingEditForm', BookingEditForm));
