// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import moment from 'moment';
import PropTypes from 'prop-types';
import shortid from 'shortid';
import {Icon, Button} from 'semantic-ui-react';
import {ANCHOR_RIGHT} from 'react-dates/constants';
import {Translate} from 'indico/react/i18n';
import {DateRangePicker} from 'indico/react/components';
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
        startDt: serializeDate(moment()),
        endDt: serializeDate(moment()),
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
        vIndex === index
          ? {...v, startDt: serializeDate(startDate), endDt: serializeDate(endDate)}
          : v
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
    const {startDt, endDt} = dateRangeItem;
    const key = shortid.generate();
    return (
      <div key={key} className="flex-container">
        <DateRangePicker
          small
          minimumNights={0}
          anchorDirection={ANCHOR_RIGHT}
          startDate={startDt === null ? null : moment(startDt)}
          endDate={endDt === null ? null : moment(endDt)}
          onDatesChange={dates => this.handleDatesChange(dates, index)}
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
