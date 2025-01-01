// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {PluralTranslate} from 'indico/react/i18n';
import {serializeTime, toMoment} from 'indico/utils/date';

import './TimeRangePicker.module.scss';

const ARROW_KEYS = ['ArrowUp', 'ArrowDown', 'Up', 'Down'];
const START_HOUR = '06:00';

function _humanizeDuration(duration) {
  const hours = duration.hours();
  const minutes = duration.minutes();
  if (hours !== 0) {
    return PluralTranslate.string('{count} hour', '{count} hours', hours + minutes / 60, {
      count: hours + minutes / 60,
    });
  } else {
    return PluralTranslate.string('{count} min', '{count} min', minutes, {count: minutes});
  }
}

function generateStartTimeOptions(minTime) {
  const options = [];
  const end = moment().endOf('day');
  const next = moment(START_HOUR, 'HH:mm');

  // eslint-disable-next-line no-unmodified-loop-condition
  while (next < end) {
    const momentNext = moment(next);
    const serializedNext = serializeTime(momentNext);
    if (momentNext >= moment(minTime, 'HH:mm')) {
      options.push({key: serializedNext, value: serializedNext, text: serializedNext});
    }
    next.add(30, 'm');
  }
  return options;
}

function generateEndTimeOptions(start) {
  const options = [];
  const end = moment().endOf('day');
  const next = moment(start).add(30, 'm');
  let duration;
  // eslint-disable-next-line no-unmodified-loop-condition
  while (next < end) {
    duration = _humanizeDuration(moment.duration(next.diff(start)));
    const serializedNext = serializeTime(moment(next));
    const text = (
      <div styleName="end-time-item">
        {serializedNext} <span styleName="duration">({duration})</span>
      </div>
    );
    options.push({key: serializedNext, value: serializedNext, text});
    next.add(30, 'm');
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

    const {startTime, endTime} = this.props;
    const duration = moment.duration(endTime.diff(startTime));
    const startSearchQuery = serializeTime(moment(startTime));
    const endSearchQuery = serializeTime(moment(endTime));
    this.state = {
      startTime,
      endTime,
      duration,
      startSearchQuery,
      endSearchQuery,
    };
  }

  shouldComponentUpdate(nextProps, nextState) {
    return nextState !== this.state || !_.isEqual(this.props, nextProps);
  }

  updateStartTime = (
    event,
    currentStartTime,
    previousStartTime,
    endTime,
    duration,
    startSearchQuery
  ) => {
    if (event.type === 'keydown' && ARROW_KEYS.includes(event.key)) {
      this.setState({
        startSearchQuery: currentStartTime,
      });
      return;
    }
    let start;
    const {onChange, minTime} = this.props;
    if (event.type === 'click') {
      start = moment(currentStartTime, ['HH:mm', 'Hmm']);
    } else {
      start = moment(startSearchQuery, ['HH:mm', 'Hmm']);
    }
    if (!start.isValid()) {
      this.setState({
        startSearchQuery: serializeTime(previousStartTime),
      });
      return;
    } else if (start < moment(minTime, 'HH:mm')) {
      this.setState({
        startSearchQuery: serializeTime(previousStartTime),
      });
      return;
    }

    let end = toMoment(endTime, 'HH:mm');
    if (end.isSameOrBefore(start, 'minute')) {
      end = moment(start).add(duration);
      if (end > moment().endOf('day')) {
        end = moment().endOf('day');
        if (start.isSame(end, 'minute')) {
          start = moment(end).subtract(duration);
        }
      }
    } else {
      duration = moment.duration(end.diff(start));
    }
    this.setState({
      startTime: start,
      endTime: end,
      startSearchQuery: serializeTime(start),
      endSearchQuery: serializeTime(end),
      duration,
    });
    onChange(start, end);
  };

  updateEndTime = (event, currentEndTime, previousEndTime, startTime, duration, endSearchQuery) => {
    if (event.type === 'keydown' && ARROW_KEYS.includes(event.key)) {
      this.setState({
        endSearchQuery: currentEndTime,
      });
      return;
    }
    let end;
    if (event.type === 'click') {
      end = moment(currentEndTime, ['HH:mm', 'Hmm']);
    } else {
      end = moment(endSearchQuery, ['HH:mm', 'Hmm']);
    }
    if (!end.isValid()) {
      this.setState({
        endSearchQuery: serializeTime(previousEndTime),
      });
      return;
    }
    let start = toMoment(startTime, 'HH:mm');
    const {onChange, minTime} = this.props;
    if (end < moment(minTime, 'HH:mm')) {
      this.setState({
        endSearchQuery: serializeTime(previousEndTime),
      });
      return;
    }
    if (end.isSameOrBefore(start, 'minute')) {
      start = moment(end).subtract(duration);
      if (start < moment().startOf('day')) {
        start = moment().startOf('day');
        if (end.isSame(start, 'minute')) {
          end = moment(start).add(duration);
        }
      } else if (start < moment(start, 'HH:mm')) {
        this.setState({
          endSearchQuery: serializeTime(previousEndTime),
        });
        return;
      }
    } else {
      duration = moment.duration(end.diff(start));
    }
    this.setState({
      startTime: start,
      endTime: end,
      startSearchQuery: serializeTime(start),
      endSearchQuery: serializeTime(end),
      duration,
    });
    onChange(start, end);
  };

  onStartSearchChange = event => {
    this.setState({
      startSearchQuery: event.target.value,
    });
  };

  onEndSearchChange = event => {
    this.setState({
      endSearchQuery: event.target.value,
    });
  };

  render() {
    const {startTime, endTime, duration, startSearchQuery, endSearchQuery} = this.state;
    const {disabled, minTime} = this.props;
    const startOptions = generateStartTimeOptions(minTime || START_HOUR);
    const endOptions = generateEndTimeOptions(startTime);
    return (
      <div styleName="time-range-picker">
        <Dropdown
          options={startOptions}
          search={() => startOptions}
          icon={null}
          selection
          styleName="start-time-dropdown"
          searchQuery={startSearchQuery}
          onSearchChange={this.onStartSearchChange}
          value={serializeTime(startTime)}
          disabled={disabled}
          onChange={(event, {value}) => {
            this.updateStartTime(event, value, startTime, endTime, duration, startSearchQuery);
          }}
        />
        <Dropdown
          options={endOptions}
          search={() => endOptions}
          icon={null}
          selection
          styleName="end-time-dropdown"
          searchQuery={endSearchQuery}
          onSearchChange={this.onEndSearchChange}
          value={serializeTime(endTime)}
          disabled={disabled}
          onChange={(event, {value}) => {
            this.updateEndTime(event, value, endTime, startTime, duration, endSearchQuery);
          }}
        />
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
