// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
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

import {SingleDatePicker, DateRangePicker} from 'indico/react/components';
import {PluralTranslate, Translate} from 'indico/react/i18n';
import {
  serializeDate,
  serializeTime,
  isBookingStartDTValid,
  createDT,
  isBookingStartDateValid,
  getMinimumBookingStartTime,
  toMoment,
  initialEndTime,
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
    buttonCaption: PropTypes.object,
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

    const startTime = moment()
      .startOf('hour')
      .add(1, 'h');
    const endTime = moment()
      .startOf('hour')
      .add(2, 'h');
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

  triggerChange() {
    const {onChange} = this.props;
    onChange(this.serializedState);
  }

  updateDates = (startDate, endDate) => {
    this.setState(
      {
        dates: {
          startDate,
          endDate,
        },
      },
      () => {
        this.triggerChange();
      }
    );
  };

  updateBookingType = newType => {
    const {
      recurrence: {number, interval, weekdays},
    } = this.state;
    const newState = {...this.state, recurrence: {type: newType, number, interval, weekdays}};
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

  onSearch = e => {
    const {onSearch} = this.props;
    onSearch(this.serializedState);
    e.preventDefault();
  };

  preselectWeekday = () => {
    const {recurrence} = this.state;
    const weekdayToday = moment()
      .locale('en')
      .format('ddd')
      .toLocaleLowerCase();

    if (recurrence.weekdays.includes(weekdayToday)) {
      return;
    }

    const weekdays = [...recurrence.weekdays, weekdayToday];
    this.setState({recurrence: {...recurrence, weekdays}});
    this.triggerChange();
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
    const recurrenceOptions = [
      {text: PluralTranslate.string('Week', 'Weeks', number), value: 'week'},
      {text: PluralTranslate.string('Month', 'Months', number), value: 'month'},
    ];
    // all but one option are hidden
    const showRecurrenceOptions =
      ['single', 'daily', 'recurring'].filter(x => hideOptions[x]).length !== 2;
    const minTime = getMinimumBookingStartTime(
      toMoment(startDate),
      isAdminOverrideEnabled,
      bookingGracePeriod
    );

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
            {!hideOptions.recurring && (
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
            <label>{Translate.string('Every')}</label>
            <Form.Input
              type="number"
              value={number}
              min="1"
              max="99"
              step="1"
              onChange={(event, data) => this.updateNumber(data.value)}
            />
            <Select
              value={interval}
              options={recurrenceOptions}
              onChange={(event, data) => this.updateInterval(data.value)}
            />
          </Form.Group>
        )}
        {['every', 'daily'].includes(type) && (
          <Form.Group inline>
            <DateRangePicker
              startDate={startDate}
              endDate={endDate}
              onDatesChange={({startDate: sd, endDate: ed}) => this.updateDates(sd, ed)}
              isOutsideRange={dt => {
                return !isBookingStartDateValid(dt, isAdminOverrideEnabled, bookingGracePeriod);
              }}
              withFullScreenPortal={window.innerHeight < 730}
            />
          </Form.Group>
        )}
        {type === 'single' && (
          <Form.Group inline>
            <SingleDatePicker
              date={startDate}
              onDateChange={date => this.updateDates(date, null)}
              disabledDate={dt => {
                return !isBookingStartDateValid(dt, isAdminOverrideEnabled, bookingGracePeriod);
              }}
              withFullScreenPortal={window.innerHeight < 730} // Temporary fix to ensure vertical responsiveness
            />
          </Form.Group>
        )}
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
          <Form.Group inline style={{marginLeft: '1em', marginRight: '1em'}}>
            <Translate as="label">Recurring every</Translate>
            <WeekdayRecurrencePicker onChange={this.updateRecurrenceWeekdays} value={weekdays} />
          </Form.Group>
        )}
        {children}
        <Button primary disabled={buttonDisabled || !isStartDtValid} onClick={this.onSearch}>
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
