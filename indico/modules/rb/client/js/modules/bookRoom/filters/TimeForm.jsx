// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {serializeTime, toMoment} from 'indico/utils/date';

import {FilterFormComponent} from '../../../common/filters';
import TimeRangePicker from '../../../components/TimeRangePicker';

import './TimeForm.module.scss';

export default class TimeForm extends FilterFormComponent {
  static propTypes = {
    startTime: PropTypes.string,
    endTime: PropTypes.string,
    minTime: PropTypes.string,
    ...FilterFormComponent.propTypes,
  };

  static defaultProps = {
    startTime: null,
    endTime: null,
    bookingGracePeriod: 1,
  };

  static getDerivedStateFromProps({startTime, endTime}, prevState) {
    // if there is no internal state, get the values from props
    return {
      startTime: toMoment(startTime, 'HH:mm'),
      endTime: toMoment(endTime, 'HH:mm'),
      ...prevState,
    };
  }

  constructor(props) {
    super(props);
    this.formRef = React.createRef();
  }

  setTimes = async (startTime, endTime) => {
    const {setParentField} = this.props;
    const {startTime: prevStartTime, endTime: prevEndTime} = this.state;

    // if everything stays the same, do nothing
    if (startTime === prevStartTime && endTime === prevEndTime) {
      return;
    }

    // send serialized versions to parent/redux
    await setParentField('startTime', serializeTime(startTime));
    await setParentField('endTime', serializeTime(endTime));

    this.setState({
      startTime,
      endTime,
    });
  };

  render() {
    const {startTime, endTime} = this.state;
    const {minTime} = this.props;
    return (
      <div ref={this.formRef}>
        <TimeRangePicker
          startTime={startTime}
          endTime={endTime}
          onChange={this.setTimes}
          minTime={minTime ? toMoment(minTime, 'HH:mm') : null}
        />
      </div>
    );
  }
}
