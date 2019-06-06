// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import {Button, Popup} from 'semantic-ui-react';
import {CalendarSingleDatePicker} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {serializeDate, toMoment} from 'indico/utils/date';
import {isDateWithinRange} from '../../util';

import './DateNavigator.module.scss';

/**
 * Component that renders a 'mode selector' (day/week/month) and a date picker.
 * This is used in timeline-style views (e.g. 'Book a Room' or 'Calendar').
 */
export default class DateNavigator extends React.Component {
  static propTypes = {
    selectedDate: PropTypes.string.isRequired,
    mode: PropTypes.string.isRequired,
    dateRange: PropTypes.array.isRequired,
    onDateChange: PropTypes.func.isRequired,
    onModeChange: PropTypes.func.isRequired,
    isLoading: PropTypes.bool,
    disabled: PropTypes.bool,
  };

  static defaultProps = {
    isLoading: false,
    disabled: false,
  };

  constructor(props) {
    super(props);
    const {mode} = this.props;
    this.setDateWithMode(this.selectedDate, mode);
  }

  state = {
    datePickerVisible: false,
  };

  componentDidUpdate(prevProps) {
    const {mode, selectedDate} = this.props;
    const {mode: prevMode, selectedDate: prevSelectedDate} = prevProps;
    if (prevMode !== mode || prevSelectedDate !== selectedDate) {
      this.setDateWithMode(this.selectedDate, mode);
    }
  }

  /**
   * Get moment representation of prop with the same name
   */
  get selectedDate() {
    const {selectedDate} = this.props;
    return toMoment(selectedDate, 'YYYY-MM-DD');
  }

  /**
   * Get moment representation of the minimum/maximum date values with the
   * current mode. That is beginning/end of week/month the booking starts/ends
   * in.
   */
  get dateBounds() {
    const {dateRange, mode} = this.props;
    if (!dateRange.length) {
      return null;
    }
    return [
      toMoment(dateRange[0], 'YYYY-MM-DD').startOf(mode),
      toMoment(dateRange[dateRange.length - 1], 'YYYY-MM-DD').startOf(mode),
    ];
  }

  /**
   * Set the currently selected date, taking into account the currently
   * selected 'interval mode'. That means rounding down to the first day of
   * the month/week.
   *
   * @param {Moment} date - selected date
   * @param {String} mode - current interval mode (days/weeks/months)
   * @param {Boolean} force - update even if the date didn't really change
   */
  setDateWithMode(date, mode, force = false) {
    const {onDateChange, dateRange} = this.props;
    let expectedDate;

    if (mode === 'weeks') {
      expectedDate = date.clone().startOf('week');
    } else if (mode === 'months') {
      expectedDate = date.clone().startOf('month');
    } else {
      expectedDate = date.clone();
      // check that we're not on a day that has no data
      if (this.dateBounds && dateRange.indexOf(serializeDate(date)) === -1) {
        expectedDate = toMoment(dateRange[0], 'YYYY-MM-DD');
      }
    }

    // check that resulting date is within bounds
    if (this.dateBounds) {
      const [minDate, maxDate] = this.dateBounds;
      if (expectedDate.isAfter(maxDate)) {
        expectedDate = maxDate.clone();
      } else if (expectedDate.isBefore(minDate)) {
        expectedDate = minDate.clone();
      }
    }

    if (force || !expectedDate.isSame(date)) {
      onDateChange(expectedDate);
    }
  }

  calendarDisabledDate = date => {
    const {dateRange} = this.props;
    if (!date) {
      return false;
    }
    return dateRange.length !== 0 && !isDateWithinRange(date, dateRange, toMoment);
  };

  onSelect = date => {
    const {mode, dateRange} = this.props;
    const freeRange = dateRange.length === 0;
    if (freeRange || isDateWithinRange(date, dateRange, toMoment)) {
      if (mode === 'weeks') {
        date = date.clone().startOf('week');
      } else if (mode === 'months') {
        date = date.clone().startOf('month');
      } else {
        date = date.clone();
      }
      this.setDateWithMode(date, mode, true);
    }
    this.onClose();
  };

  changeSelectedDate = direction => {
    const {selectedDate, dateRange, onDateChange, mode} = this.props;
    const step = direction === 'next' ? 1 : -1;

    // dateRange is not set (unlimited)
    if (dateRange.length === 0 || mode !== 'days') {
      onDateChange(this.selectedDate.clone().add(step, mode));
    } else {
      const index = dateRange.findIndex(dt => dt === selectedDate) + step;
      onDateChange(toMoment(dateRange[index]));
    }
  };

  handleModeChange = mode => {
    const {onModeChange} = this.props;
    onModeChange(mode);
    this.setDateWithMode(this.selectedDate, mode);
  };

  renderModeSwitcher(disabled) {
    const {mode} = this.props;
    return (
      !!mode && (
        <Button.Group size="tiny" styleName="date-navigator-item">
          <Button
            content={Translate.string('Day')}
            onClick={() => this.handleModeChange('days')}
            primary={mode === 'days'}
            disabled={disabled}
          />
          <Button
            content={Translate.string('Week')}
            onClick={() => this.handleModeChange('weeks')}
            primary={mode === 'weeks'}
            disabled={disabled}
          />
          <Button
            content={Translate.string('Month')}
            onClick={() => this.handleModeChange('months')}
            primary={mode === 'months'}
            disabled={disabled}
          />
        </Button.Group>
      )
    );
  }

  onOpen = () => {
    this.setState({datePickerVisible: true});
  };

  onClose = () => {
    this.setState({datePickerVisible: false});
  };

  /**
   * Check whether a given date change (back/forward) would result
   * in a valid situation or not.
   *
   * @param {Number} num - the number of units to look forward
   * @param {String} mode - the type of unit (days/weeks/months)
   */
  isValidChange(num, mode) {
    // if we're not limited, any date is valid
    if (!this.dateBounds) {
      return true;
    }

    const [minDate, maxDate] = this.dateBounds;
    const targetDate = this.selectedDate.clone().add(num, mode);

    if (targetDate.isAfter(maxDate)) {
      return false;
    } else if (targetDate.isBefore(minDate)) {
      return false;
    }
    return true;
  }

  /**
   * Render the DateNavigator, with its prev/next arrows.
   *
   * @param {Boolean} disabled - whether to render the navigator as disabled
   */
  renderNavigator(disabled) {
    const {mode} = this.props;
    const {datePickerVisible} = this.state;

    const calendarPicker = (
      <Popup
        on="click"
        position="bottom left"
        open={datePickerVisible}
        onOpen={this.onOpen}
        onClose={this.onClose}
        trigger={
          <Button primary disabled={disabled}>
            {mode === 'days' && this.selectedDate.format('L')}
            {mode === 'months' && this.selectedDate.format('MMMM YYYY')}
            {mode === 'weeks' &&
              Translate.string('Week of {date}', {
                date: this.selectedDate.format('MMM Do YYYY'),
              })}
          </Button>
        }
        content={
          <CalendarSingleDatePicker
            date={this.selectedDate}
            onDateChange={this.onSelect}
            disabledDate={this.calendarDisabledDate}
            noBorder
          />
        }
        hideOnScroll
      />
    );
    const prevDisabled = disabled || !this.isValidChange(-1, mode);
    const nextDisabled = disabled || !this.isValidChange(1, mode);

    return (
      <Button.Group size="tiny" styleName="date-navigator-item">
        <Button
          icon="left arrow"
          onClick={() => this.changeSelectedDate('prev')}
          disabled={prevDisabled}
        />
        {calendarPicker}
        <Button
          icon="right arrow"
          onClick={() => this.changeSelectedDate('next')}
          disabled={nextDisabled}
        />
      </Button.Group>
    );
  }

  render = () => {
    const {dateRange, disabled, isLoading} = this.props;
    return (
      <div styleName="date-navigator">
        {this.renderModeSwitcher(disabled || isLoading)}
        {this.renderNavigator(disabled || isLoading || dateRange.length === 1)}
      </div>
    );
  };
}
