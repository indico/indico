// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import Overridable from 'react-overridable';
import {connect} from 'react-redux';
import {Button, Form, Select} from 'semantic-ui-react';

import {DatePicker, DateRangePicker} from 'indico/react/components';
import {INVALID} from 'indico/react/components/DatePicker';
import {PluralTranslate, Translate} from 'indico/react/i18n';
import {
  serializeDate,
  serializeTime,
  isBookingStartDTValid,
  createDT,
  getMinimumBookingStartTime,
  toMoment,
  initialEndTime,
  getBookingRangeMinDate,
} from 'indico/utils/date';

import {selectors as configSelectors} from '../common/config';
import {selectors as userSelectors} from '../common/user';
import {sanitizeRecurrence} from '../util';

import TimeRangePicker from './TimeRangePicker';
import WeekdayRecurrencePicker from './WeekdayRecurrencePicker';

import './BookingBootstrapForm.module.scss';

class BookingBootstrapForm extends React.Component {
  // eslint-disable-next-line react/sort-comp
  static propTypes = {
    onSearch: PropTypes.func.isRequired,
    onChange: PropTypes.func,
    buttonCaption: PropTypes.oneOfType([PropTypes.string, PropTypes.element]),
    children: PropTypes.node,
    buttonDisabled: PropTypes.bool,
    dayBased: PropTypes.bool,
    hideOptions: PropTypes.objectOf(PropTypes.bool),
    defaults: PropTypes.object,
    isAdminOverrideEnabled: PropTypes.bool.isRequired,
    bookingGracePeriod: PropTypes.number,
  };

  static get defaultProps() {
    return {
      children: null,
      buttonCaption: <Translate>Search</Translate>,
      onChange: () => {},
      buttonDisabled: false,
      dayBased: false,
      hideOptions: {},
      defaults: {},
      bookingGracePeriod: null,
    };
  }

  constructor(props) {
    super(props);

    const startTime = moment().startOf('hour').add(1, 'h');
    const endTime = moment().startOf('hour').add(2, 'h');
    const startsNextDay = startTime > moment().endOf('day');

    const {defaults} = props;
    this.state = _.merge(
      {
        recurrence: {
          type: 'single',
          number: 1,
          interval: 'week',
          weekdays: [],
        },
        dates: {
          startDate: startsNextDay ? moment().add(1, 'd') : moment(),
          endDate: null,
        },
        invalidDates: {start: false, end: false},
        timeSlot: {
          startTime,
          endTime: startsNextDay ? endTime : initialEndTime(endTime),
        },
      },
      defaults
    );
  }

  componentDidMount() {
    this.triggerChange();
  }

  componentDidUpdate() {
    const {recurrence} = this.state;
    if (
      recurrence.type === 'every' &&
      recurrence.interval === 'week' &&
      recurrence.weekdays.length === 0
    ) {
      this.preselectWeekday();
    }
  }

  updateIntervalOptions = () => {
    const {hideOptions} = this.props;
    const {recurrence} = this.state;

    if (!hideOptions.recurringWeekly && !hideOptions.recurringMonthly) {
      return null;
    }

    if (hideOptions.recurringWeekly && recurrence.interval !== 'month') {
      this.updateInterval('month');
    }

    if (hideOptions.recurringMonthly && recurrence.interval !== 'week') {
      this.updateInterval('week');
    }
  };

  triggerChange() {
    const {onChange} = this.props;
    const {startError, endError} = this.dateErrors;
    onChange(this.serializedState, Boolean(startError || endError));
  }

  updateDates = (startDate, endDate) => {
    this.setState(
      {
        dates: {
          startDate: startDate === INVALID ? null : toMoment(startDate, 'YYYY-MM-DD'),
          endDate: endDate === INVALID ? null : toMoment(endDate, 'YYYY-MM-DD'),
        },
        invalidDates: {start: startDate === INVALID, end: endDate === INVALID},
      },
      () => {
        this.triggerChange();
      }
    );
  };

  updateBookingType = newType => {
    const {
      recurrence: {type, number, interval, weekdays},
    } = this.state;
    const newState = {...this.state, recurrence: {type: newType, number, interval, weekdays}};
    if (type === 'single' || newType === 'single') {
      newState.invalidDates = {start: false, end: false};
    }
    sanitizeRecurrence(newState);
    this.setState(newState, () => {
      this.triggerChange();
    });
  };

  updateNumber = number => {
    const {
      recurrence: {type, interval, weekdays},
    } = this.state;
    this.setState({number});
    this.setState(
      {
        recurrence: {type, number: parseInt(number, 10), interval, weekdays},
      },
      () => {
        this.triggerChange();
      }
    );
  };

  updateInterval = interval => {
    const {
      recurrence: {type, number, weekdays},
    } = this.state;

    // Clear weekdays if interval is changed to month
    const updatedWeekdays = interval === 'month' ? [] : weekdays;

    this.setState(
      {
        recurrence: {type, number, interval, weekdays: updatedWeekdays},
      },
      () => {
        this.triggerChange();
      }
    );
  };

  updateTimes = (startTime, endTime) => {
    this.setState(
      {
        timeSlot: {
          startTime,
          endTime,
        },
      },
      () => {
        this.triggerChange();
      }
    );
  };

  updateRecurrenceWeekdays = selectedDays => {
    const {
      recurrence: {type, number, interval},
    } = this.state;
    this.setState(
      {
        recurrence: {type, number, interval, weekdays: selectedDays},
      },
      () => {
        this.triggerChange();
      }
    );
  };

  get serializedState() {
    const {dayBased} = this.props;
    const {
      timeSlot: {startTime, endTime},
      dates: {startDate, endDate},
      recurrence,
    } = this.state;

    const state = {
      recurrence,
      dates: {
        startDate: serializeDate(startDate),
        endDate: serializeDate(endDate),
      },
      weekdays: recurrence.weekdays,
    };

    if (!dayBased) {
      state.timeSlot = {
        startTime: serializeTime(startTime),
        endTime: serializeTime(endTime),
      };
    }
    return state;
  }

  get dateErrors() {
    const {isAdminOverrideEnabled, bookingGracePeriod} = this.props;
    const {
      dates: {startDate, endDate},
      recurrence: {type},
      invalidDates,
    } = this.state;
    const format = moment.localeData().longDateFormat('L');
    const min = getBookingRangeMinDate(isAdminOverrideEnabled, bookingGracePeriod);
    let startError = '';
    let endError = '';
    if (invalidDates.start) {
      startError =
        type === 'single'
          ? Translate.string('Enter a valid date in the format {format}.', {format})
          : Translate.string('Enter a valid start date in the format {format}.', {format});
    } else if (!startDate) {
      startError =
        type === 'single'
          ? Translate.string('Enter a booking date.')
          : Translate.string('Please provide the start date');
    } else if (min && serializeDate(startDate) < min) {
      startError = Translate.string('The entered date cannot be earlier than {min}.', {
        min: moment(min).format(format),
      });
    }
    if (type !== 'single') {
      if (invalidDates.end) {
        endError = Translate.string('Enter a valid end date in the format {format}.', {format});
      } else if (!endDate) {
        endError = Translate.string('Please provide the end date');
      } else if (startDate && endDate.isBefore(startDate, 'day')) {
        endError = Translate.string('The end date cannot be earlier than the start date.');
      }
    }
    return {startError, endError};
  }

  onSearch = e => {
    const {onSearch} = this.props;
    onSearch(this.serializedState);
    e.preventDefault();
  };

  preselectWeekday = () => {
    const {recurrence} = this.state;
    const weekdayToday = moment().locale('en').format('ddd').toLocaleLowerCase();

    if (recurrence.weekdays.includes(weekdayToday)) {
      return;
    }

    const weekdays = [...recurrence.weekdays, weekdayToday];
    this.setState({recurrence: {...recurrence, weekdays}});
    this.triggerChange();
  };

  getRecurrenceOptions = () => {
    const {hideOptions} = this.props;
    const {recurrence} = this.state;

    if (hideOptions.recurringWeekly && hideOptions.recurringMonthly) {
      return null;
    }

    if (hideOptions.recurringWeekly) {
      return [{text: PluralTranslate.string('Month', 'Months', recurrence.number), value: 'month'}];
    }

    if (hideOptions.recurringMonthly) {
      return [{text: PluralTranslate.string('Week', 'Weeks', recurrence.number), value: 'week'}];
    }

    return [
      {text: PluralTranslate.string('Week', 'Weeks', recurrence.number), value: 'week'},
      {text: PluralTranslate.string('Month', 'Months', recurrence.number), value: 'month'},
    ];
  };

  render() {
    const {
      timeSlot: {startTime, endTime},
      recurrence: {type, number, interval, weekdays},
      dates: {startDate, endDate},
    } = this.state;

    const {
      buttonCaption,
      buttonDisabled,
      children,
      dayBased,
      hideOptions,
      isAdminOverrideEnabled,
      bookingGracePeriod,
    } = this.props;
    const isStartDtValid = isBookingStartDTValid(
      createDT(startDate, startTime),
      isAdminOverrideEnabled,
      bookingGracePeriod
    );
    // all but one option are hidden
    const showRecurrenceOptions =
      ['single', 'daily', 'recurring'].filter(x => hideOptions[x]).length !== 2;
    const minTime = getMinimumBookingStartTime(
      toMoment(startDate),
      isAdminOverrideEnabled,
      bookingGracePeriod
    );
    const recurrenceHidden = hideOptions.recurringWeekly && hideOptions.recurringMonthly;
    const {startError, endError} = this.dateErrors;

    return (
      <Form>
        {showRecurrenceOptions && (
          <Form.Group inline styleName="booking-type-field">
            {!hideOptions.single && (
              <Form.Radio
                label={Translate.string('Single booking')}
                name="type"
                value="single"
                checked={type === 'single'}
                onChange={(e, {value}) => this.updateBookingType(value)}
              />
            )}
            {!hideOptions.daily && (
              <Form.Radio
                label={Translate.string('Daily booking')}
                name="type"
                value="daily"
                checked={type === 'daily'}
                onChange={(e, {value}) => this.updateBookingType(value)}
              />
            )}
            {!recurrenceHidden && (
              <Form.Radio
                label={Translate.string('Recurring booking')}
                name="type"
                value="every"
                checked={type === 'every'}
                onChange={(e, {value}) => this.updateBookingType(value)}
              />
            )}
          </Form.Group>
        )}
        {type === 'every' && (
          <Form.Group inline styleName="recurrence-field">
            <label>{Translate.string('Every', 'Repetition')}</label>
            <Form.Input
              type="number"
              value={number}
              min="1"
              max="99"
              step="1"
              onChange={(event, data) => this.updateNumber(data.value)}
            />
            {hideOptions.recurringWeekly || hideOptions.recurringMonthly ? (
              <label>{this.getRecurrenceOptions().map(x => x.text)}</label>
            ) : (
              <Select
                value={interval}
                options={this.getRecurrenceOptions()}
                disabled={recurrenceHidden}
                onChange={(event, data) => this.updateInterval(data.value)}
              />
            )}
            {this.updateIntervalOptions()}
          </Form.Group>
        )}
        <Form.Group inline>
          {type === 'single' ? (
            <DatePicker
              required
              label={Translate.string('Booking date')}
              calendarLabel={Translate.string('Booking calendar')}
              min={getBookingRangeMinDate(isAdminOverrideEnabled, bookingGracePeriod)}
              value={serializeDate(startDate)}
              error={startError}
              onChange={date => this.updateDates(date, null)}
            />
          ) : (
            <DateRangePicker
              required
              calendarLabel={Translate.string('Booking date range calendar')}
              min={getBookingRangeMinDate(isAdminOverrideEnabled, bookingGracePeriod)}
              value={{startDate: serializeDate(startDate), endDate: serializeDate(endDate)}}
              startError={startError}
              endError={endError}
              onChange={({startDate: sd, endDate: ed}) => this.updateDates(sd, ed)}
            />
          )}
        </Form.Group>
        <output styleName="date-errors">
          {startError && <span>{startError}</span>}
          {endError && <span>{endError}</span>}
        </output>
        {!dayBased && (
          <Form.Group inline>
            <TimeRangePicker
              startTime={startTime}
              endTime={endTime}
              onChange={this.updateTimes}
              minTime={minTime}
            />
          </Form.Group>
        )}
        {type === 'every' && interval === 'week' && (
          <Form.Group inline>
            <Translate as="label">Recurring every</Translate>
            <WeekdayRecurrencePicker onChange={this.updateRecurrenceWeekdays} value={weekdays} />
          </Form.Group>
        )}
        {children}
        <Button
          primary
          disabled={buttonDisabled || !isStartDtValid || !!startError || !!endError}
          onClick={this.onSearch}
        >
          {buttonCaption}
        </Button>
      </Form>
    );
  }
}

export default connect(state => ({
  isAdminOverrideEnabled: userSelectors.isUserAdminOverrideEnabled(state),
  bookingGracePeriod: configSelectors.getBookingGracePeriod(state),
}))(Overridable.component('BookingBootstrapForm', BookingBootstrapForm));
