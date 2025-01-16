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
import {Icon, Button} from 'semantic-ui-react';

import {DateRangePicker} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';
import {serializeDate} from 'indico/utils/date';

export default class NonBookablePeriods extends React.Component {
  static propTypes = {
    onFocus: PropTypes.func.isRequired,
    onBlur: PropTypes.func.isRequired,
    onChange: PropTypes.func.isRequired,
    value: PropTypes.array,
  };

  static defaultProps = {
    value: [],
  };

  handleAddDates = () => {
    const {value, onChange} = this.props;
    onChange([
      ...value,
      {
        start_dt: serializeDate(moment()),
        end_dt: serializeDate(moment()),
      },
    ]);
    this.setTouched();
  };

  handleRemoveDates = index => {
    const {value, onChange} = this.props;
    onChange(value.filter((_, i) => i !== index));
    this.setTouched();
  };

  handleDatesChange = ({startDate, endDate}, index) => {
    const {value, onChange} = this.props;
    onChange(
      value.map((v, vIndex) =>
        vIndex === index ? {...v, start_dt: startDate, end_dt: endDate} : v
      )
    );
    this.setTouched();
  };

  setTouched = () => {
    // pretend focus+blur to mark the field as touched in case an action changes
    // the data without actually involving focus and blur of a form element
    const {onFocus, onBlur} = this.props;
    onFocus();
    onBlur();
  };

  renderEntry = (dateRangeItem, index) => {
    const {start_dt: startDt, end_dt: endDt} = dateRangeItem;
    const key = nanoid();
    return (
      <div key={key} className="flex-container">
        <DateRangePicker
          value={{startDate: startDt, endDate: endDt}}
          onChange={dates => this.handleDatesChange(dates, index)}
          min={serializeDate(moment())}
        />
        <Icon
          floated="right"
          name="remove"
          className="delete-button"
          onClick={() => this.handleRemoveDates(index)}
        />
      </div>
    );
  };

  render() {
    const {value} = this.props;
    return (
      <>
        <Button
          type="button"
          className="room-edit-modal-add-btn"
          icon
          labelPosition="left"
          onClick={this.handleAddDates}
        >
          <Icon name="plus" />
          <Translate>Add new Nonbookable Periods</Translate>
        </Button>
        {value && value.map(this.renderEntry)}
        {value.length === 0 && (
          <div>
            <Translate>No non-bookable periods found</Translate>
          </div>
        )}
      </>
    );
  }
}
