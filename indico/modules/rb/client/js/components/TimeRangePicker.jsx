// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';

import {ComboBox} from 'indico/react/components';
import {FinalField} from 'indico/react/forms';
import {PluralTranslate, Translate} from 'indico/react/i18n';
import {serializeTime, toMoment} from 'indico/utils/date';

import './TimeRangePicker.module.scss';

// FIXME: Alignment of time options in the list

const START_HOUR = '06:00';
const ALLOWED_INPUT_FORMATS = ['HH:mm', 'HHmm', 'H:mm', 'Hmm'];
const MIN_DURATION = moment.duration(30, 'minutes');

function _humanizeDuration(duration) {
  const minutes = duration.minutes();
  const hours = duration.hours() + minutes / 60;
  if (hours < 1) {
    return PluralTranslate.string('{time} min', '{time} min', minutes, {time: minutes});
  }
  return PluralTranslate.string('{time} hour', '{time} hours', hours, {time: hours});
}

function generateStartTimeOptions(minTime) {
  // The options for the start time is an array of strings.
  // Even though the minTime is specified, it is capped at
  // START_HOUR, so options before START_HOUR are not shown
  // even though they are allowed.
  const options = [];
  let next = moment.max(moment(START_HOUR, 'HH:mm'), minTime);
  const end = moment().endOf('day');
  while (next < end) {
    options.push(serializeTime(next));
    next = next.add(MIN_DURATION);
  }
  return options;
}

function generateEndTimeOptions(start) {
  // The labels for end time options include a duration
  // so the option array contains objects with `value` and
  // `label` properties. The end time options start 30
  // minutes after the start time.
  const options = [];
  const end = moment().endOf('day');
  let next = moment(start).add(MIN_DURATION);
  while (next < end) {
    const duration = _humanizeDuration(moment.duration(next.diff(start)));
    const value = serializeTime(moment(next));
    const label = (
      <div styleName="end-time-item">
        {value} <span styleName="duration">({duration})</span>
      </div>
    );
    options.push({value, label});
    next = next.add(MIN_DURATION);
  }
  return options;
}

export default class TimeRangePicker extends React.Component {
  static propTypes = {
    startTime: PropTypes.object.isRequired,
    endTime: PropTypes.object.isRequired,
    onChange: PropTypes.func.isRequired,
    disabled: PropTypes.bool,
    minTime: PropTypes.string,
  };

  static defaultProps = {
    disabled: false,
    minTime: '00:00',
  };

  constructor(props) {
    super(props);

    const {startTime, endTime, minTime} = this.props;
    const duration = moment.duration(endTime.diff(startTime));
    const startInputValue = serializeTime(moment(startTime));
    const endInputValue = serializeTime(moment(endTime));
    this.minTime = moment(minTime ?? '00:00', 'HH:mm');
    this.state = {
      startTime,
      endTime,
      duration,
      startInputValue,
      endInputValue,
      startTimeOptions: generateStartTimeOptions(this.minTime || START_HOUR),
      endTimeOptions: generateEndTimeOptions(startTime),
      promptText: '',
    };
  }

  shouldComponentUpdate(nextProps, nextState) {
    return nextState !== this.state || !_.isEqual(this.props, nextProps);
  }

  parseUserInputAsTime = value => {
    return moment(value, ALLOWED_INPUT_FORMATS, true);
  };

  // Set the new start time from user input
  updateStartTime = evt => {
    this.setState({
      startInputValue: evt.target.value,
    });
    const startTime = this.parseUserInputAsTime(evt.target.value);

    if (!startTime.isValid()) {
      return;
    }

    if (startTime < this.minTime) {
      return;
    }

    this.setState({
      startTime,
      endTimeOptions: generateEndTimeOptions(startTime),
      promptText: serializeTime(startTime),
    });

    const {onChange} = this.props;
    const {endTime} = this.state;
    onChange(startTime, endTime);
  };

  // Set the new end time from user input and optionally nudge the start time
  updateEndTime = evt => {
    this.setState({
      endInputValue: evt.target.value,
    });
    const endTime = this.parseUserInputAsTime(evt.target.value);

    if (!endTime.isValid()) {
      return;
    }

    this.setState({
      endTime,
      promptText: serializeTime(endTime),
    });

    const {onChange} = this.props;
    const {startTime} = this.state;
    onChange(startTime, endTime);
  };

  // When user leaves the start time field, fix the time formatting
  // and optionally adjust the end time.
  fixStartTime = () => {
    const {startTime} = this.state;

    this.setState({
      startInputValue: serializeTime(startTime),
    });

    // Do we need to nudge the end time?
    let {endTime} = this.state;
    if (startTime > endTime) {
      const {duration} = this.state;
      endTime = moment(startTime).add(duration);
      this.setState({
        endTime,
        endInputValue: serializeTime(endTime),
        promptText: Translate.string('end time is adjusted to {endTime}', {
          endTime: serializeTime(endTime),
        }),
        duration: moment.duration(endTime.diff(startTime)),
      });
      const {onChange} = this.props;
      onChange(startTime, endTime);
    } else {
      this.setState({
        duration: moment.duration(endTime.diff(startTime)),
      });
    }
  };

  // When user leaves the end time field, fix the time formatting,
  // and optionally adjust the start time.
  fixEndTime = () => {
    const {endTime} = this.state;

    this.setState({
      endInputValue: serializeTime(endTime),
    });

    // Do we need to nudge the start time?
    let {startTime} = this.state;
    if (endTime < startTime) {
      const {duration} = this.state;
      startTime = moment(endTime).subtract(duration);
      if (startTime < this.minTime) {
        startTime = moment(this.minTime);
      }
      this.setState({
        startTime,
        startInputValue: serializeTime(startTime),
        promptText: Translate.string('start time is adjusted to {startTime}', {
          startTime: serializeTime(startTime),
        }),
      });
      const {onChange} = this.props;
      onChange(startTime, endTime);
    } else {
      this.setState({
        duration: moment.duration(endTime.diff(startTime)),
      });
    }
  };

  onStartSearchChange = event => {
    this.setState({
      startInputValue: event.target.value,
    });
  };

  onEndSearchChange = event => {
    this.setState({
      endInputValue: event.target.value,
    });
  };

  render() {
    const {
      startInputValue,
      endInputValue,
      startTimeOptions,
      endTimeOptions,
      promptText,
    } = this.state;
    const {disabled} = this.props;

    return (
      <div styleName="time-range-picker">
        <ComboBox
          onChange={this.updateStartTime}
          onBlur={this.fixStartTime}
          options={startTimeOptions}
          value={startInputValue}
          disabled={disabled}
        />
        <ComboBox
          onChange={this.updateEndTime}
          onBlur={this.fixEndTime}
          options={endTimeOptions}
          value={endInputValue}
          disabled={disabled}
        />

        <div styleName="prompt" aria-live="polite">
          {/* Prompt text is used to provide cues to the screen readers
              about how the entered input is going to be interpreted
              by the application. */}
          {promptText}
        </div>
      </div>
    );
  }
}

function ValuedTimeRangePicker({value, onChange, ...rest}) {
  const startTime = toMoment(value.startTime, 'HH:mm');
  const endTime = toMoment(value.endTime, 'HH:mm');
  const handleChange = (start, end) => {
    onChange({
      startTime: serializeTime(start),
      endTime: serializeTime(end),
    });
  };
  return (
    <TimeRangePicker startTime={startTime} endTime={endTime} onChange={handleChange} {...rest} />
  );
}

ValuedTimeRangePicker.propTypes = {
  value: PropTypes.exact({
    startTime: PropTypes.string.isRequired,
    endTime: PropTypes.string.isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};

/**
 * Like `FinalField` but for a `TimeRangePicker`.
 */
export function FinalTimeRangePicker({name, ...rest}) {
  return <FinalField name={name} component={ValuedTimeRangePicker} isEqual={_.isEqual} {...rest} />;
}

FinalTimeRangePicker.propTypes = {
  name: PropTypes.string.isRequired,
};
