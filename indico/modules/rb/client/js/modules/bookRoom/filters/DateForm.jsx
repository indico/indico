// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';

import {CalendarSingleDatePicker, CalendarRangeDatePicker} from 'indico/react/components';
import {serializeDate, toMoment} from 'indico/utils/date';

import {FilterFormComponent} from '../../../common/filters';

export default class DateForm extends FilterFormComponent {
  static propTypes = {
    startDate: PropTypes.string,
    endDate: PropTypes.string,
    isRange: PropTypes.bool.isRequired,
    disabledDate: PropTypes.func,
    ...FilterFormComponent.propTypes,
  };

  static defaultProps = {
    startDate: null,
    endDate: null,
    disabledDate: null,
  };

  static getDerivedStateFromProps({startDate, endDate}, prevState) {
    // if there is no internal state, get the values from props
    return {
      startDate: prevState.startDate || toMoment(startDate),
      endDate: prevState.endDate || toMoment(endDate),
      ...prevState,
    };
  }

  setDates(startDate, endDate) {
    // return a promise that awaits the state update
    return new Promise(resolve => {
      const {setParentField} = this.props;
      // send serialized versions to parent/redux
      setParentField('startDate', serializeDate(startDate));
      setParentField('endDate', serializeDate(endDate));
      this.setState(
        {
          startDate,
          endDate,
        },
        () => {
          resolve();
        }
      );
    });
  }

  disabledDate(current) {
    if (current) {
      return current.isBefore(moment(), 'day');
    }
  }

  render() {
    const {isRange, disabledDate} = this.props;
    const {startDate, endDate} = this.state;
    const picker = isRange ? (
      <CalendarRangeDatePicker
        startDate={startDate}
        endDate={endDate}
        onDatesChange={async ({startDate: sd, endDate: ed}) => {
          await this.setDates(sd, ed);
        }}
        disabledDate={disabledDate || this.disabledDate}
        noBorder
      />
    ) : (
      <CalendarSingleDatePicker
        date={startDate}
        yearsBefore={0}
        yearsAfter={1}
        onDateChange={async date => {
          await this.setDates(date, null);
        }}
        disabledDate={disabledDate || this.disabledDate}
        noBorder
      />
    );

    return <div className="ui form">{picker}</div>;
  }
}
