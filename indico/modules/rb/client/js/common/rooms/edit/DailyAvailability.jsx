// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import {nanoid} from 'nanoid';
import PropTypes from 'prop-types';
import React from 'react';
import {Button, Dropdown, Icon} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';
import {serializeTime} from 'indico/utils/date';

import TimeRangePicker from '../../../components/TimeRangePicker';

import './DailyAvailability.module.scss';

export default class DailyAvailability extends React.Component {
  static propTypes = {
    onChange: PropTypes.func.isRequired,
    value: PropTypes.arrayOf(PropTypes.object),
  };

  static defaultProps = {
    value: [],
  };

  handleTimesChange = ({startTime, endTime}, index) => {
    const {value, onChange} = this.props;
    onChange(
      value.map((v, vIndex) =>
        vIndex === index
          ? {...v, start_time: serializeTime(startTime), end_time: serializeTime(endTime)}
          : v
      )
    );
  };

  handleWeekdayChange = (weekday, index) => {
    const {value, onChange} = this.props;
    onChange(value.map((v, vIndex) => (vIndex === index ? {...v, weekday} : v)));
  };

  handleRemoveTimes = index => {
    const {onChange, value} = this.props;
    onChange(value.filter((__, i) => i !== index));
  };

  renderEntry = (bookableHour, index) => {
    const {start_time: startT, end_time: endT, weekday} = bookableHour;
    const key = nanoid();
    const weekdayOptions = moment.weekdays(true).map(wd => ({
      value: moment().day(wd).locale('en').format('ddd').toLowerCase(),
      text: moment().isoWeekday(wd).format('ddd'),
    }));

    return (
      <div key={key} className="flex-container">
        <Dropdown
          options={weekdayOptions}
          value={weekday}
          onChange={(__, {value: day}) => this.handleWeekdayChange(day || null, index)}
          placeholder={Translate.string('All days')}
          styleName="weekday-selector"
          selectOnBlur={false}
          selectOnNavigation={false}
          selection
          clearable
          compact
        />
        <TimeRangePicker
          startTime={moment(startT, 'HH:mm')}
          endTime={moment(endT, 'HH:mm')}
          onChange={(startTime, endTime) => this.handleTimesChange({startTime, endTime}, index)}
        />
        <Icon
          floated="right"
          name="remove"
          className="delete-button"
          onClick={() => this.handleRemoveTimes(index)}
        />
      </div>
    );
  };

  render() {
    const {value, onChange} = this.props;
    return (
      <>
        <Button
          type="button"
          className="room-edit-modal-add-btn"
          icon
          labelPosition="left"
          onClick={() =>
            onChange([...value, {start_time: '08:00', end_time: '17:00', weekday: null}])
          }
        >
          <Icon name="plus" />
          <Translate>Add new Daily Availability</Translate>
        </Button>
        {value && value.map(this.renderEntry)}
        {value.length === 0 && (
          <div>
            <Translate>No daily availability found</Translate>
          </div>
        )}
      </>
    );
  }
}
