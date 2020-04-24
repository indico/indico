// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import PropTypes from 'prop-types';
import moment from 'moment';
import shortid from 'shortid';
import {Button, Icon} from 'semantic-ui-react';
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

  handleRemoveTimes = index => {
    const {onChange, value} = this.props;
    onChange(value.filter((__, i) => i !== index));
  };

  renderEntry = (bookableHour, index) => {
    const {start_time: startT, end_time: endT} = bookableHour;
    const key = shortid.generate();
    return (
      <div key={key} className="flex-container">
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
          onClick={() => onChange([...value, {start_time: '08:00', end_time: '17:00'}])}
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
