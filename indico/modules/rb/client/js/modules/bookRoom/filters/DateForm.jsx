// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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
    minDate: PropTypes.string,
    ...FilterFormComponent.propTypes,
  };

  static defaultProps = {
    startDate: null,
    endDate: null,
    minDate: null,
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

  render() {
    const {isRange, minDate} = this.props;
    const {startDate, endDate} = this.state;

    const picker = isRange ? (
      <CalendarRangeDatePicker
        startDate={serializeDate(startDate)}
        endDate={serializeDate(endDate)}
        minDate={serializeDate(minDate)}
        onChange={({startDate: sd, endDate: ed}) =>
          this.setDates(toMoment(sd, 'YYYY-MM-DD'), toMoment(ed, 'YYYY-MM-DD'))
        }
      />
    ) : (
      <CalendarSingleDatePicker
        date={serializeDate(startDate)}
        minDate={serializeDate(minDate)}
        onChange={date => this.setDates(toMoment(date, 'YYYY-MM-DD'), null)}
      />
    );

    return <div className="ui form">{picker}</div>;
  }
}
