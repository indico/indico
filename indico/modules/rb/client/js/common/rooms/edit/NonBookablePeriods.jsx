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

import './NonBookablePeriods.module.scss';

const idField = Symbol('id');

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

  /**
   * Set an internal identifier for the date range item that will be used to identify
   * the associated form control.
   *
   * The value can be specified if you want to use a specific value (e.g., when copying
   * an existing date range item object). Otherwise it defaults to a random string that
   * looks like '0.an017nf0jas'.
   */
  setIdField(dateRangeItem, value = nanoid()) {
    dateRangeItem[idField] = value;
    return dateRangeItem;
  }

  /**
   * Inject ids into the existing values if necessary.
   *
   * This fixup is necessary when dealing with two cases:
   *
   * 1. On initial load, when there's already data in the backend.
   * 2. After form submission when the data in the local state store is refreshed.
   *
   * The date range items in the 'value' prop will be given an Symbol('id') field,
   * which will be used internally te track the UI-data association. This is usually
   * missing/destroyed in the cases mentioned before.
   *
   * This mutates the objects in-place, and relies on the fact that the rest of the app
   * won't care about that. It's a reasonable assumption because we're using a Symbol
   * as the key.
   */
  fixValues() {
    const {value} = this.props;
    for (const dateRangeItem of value) {
      if (!dateRangeItem[idField]) {
        this.setIdField(dateRangeItem);
      }
    }
  }

  handleAddDates = () => {
    const {value, onChange} = this.props;
    const date = moment();
    // find the first date that is NOT in the list yet to avoid react key collisions
    while (
      value.some(v => v.start_dt === serializeDate(date) && v.end_dt === serializeDate(date))
    ) {
      date.add(1, 'day');
    }
    onChange([
      ...value,
      this.setIdField({
        start_dt: serializeDate(date),
        end_dt: serializeDate(date),
      }),
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
        vIndex === index ? this.setIdField({start_dt: startDate, end_dt: endDate}, v[idField]) : v
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
    const {start_dt: startDt, end_dt: endDt, [idField]: key} = dateRangeItem;
    return (
      <div key={key} className="flex-container" styleName="NonBookablePeriods">
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
    this.fixValues();

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
