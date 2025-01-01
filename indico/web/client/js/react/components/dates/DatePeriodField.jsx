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
import {START_DATE, END_DATE} from 'react-dates/constants';

import {DateRangePicker} from 'indico/react/components';
import {serializeDate} from 'indico/utils/date';

import {FinalField, validators as v} from '../../forms';

import './DatePeriodField.module.scss';

export default class DatePeriodField extends React.Component {
  static propTypes = {
    disabledDate: PropTypes.func,
    onChange: PropTypes.func.isRequired,
    onFocus: PropTypes.func.isRequired,
    onBlur: PropTypes.func.isRequired,
    onFieldFocusChange: PropTypes.func,
    readOnly: PropTypes.bool,
    disabled: PropTypes.bool,
    disabledDateFields: PropTypes.oneOf([START_DATE, END_DATE]),
    value: PropTypes.shape({
      startDate: PropTypes.string,
      endDate: PropTypes.string,
    }),
    minimumDays: PropTypes.number,
    initialVisibleMonth: PropTypes.func,
    extraPickerProps: PropTypes.object,
  };

  static defaultProps = {
    readOnly: false,
    disabledDate: null,
    disabled: false,
    disabledDateFields: null,
    value: null,
    minimumDays: 1,
    initialVisibleMonth: null,
    onFieldFocusChange: null,
    extraPickerProps: {},
  };

  state = {
    focused: null,
  };

  shouldComponentUpdate(nextProps, nextState) {
    const {disabled: prevDisabled, value: prevValue} = this.props;
    const {disabled, value} = nextProps;
    return nextState !== this.state || disabled !== prevDisabled || !_.isEqual(prevValue, value);
  }

  getMomentValue(type) {
    const {value} = this.props;
    if (!value || !value[type]) {
      return null;
    }
    return moment(value[type], 'YYYY-MM-DD');
  }

  notifyChange = ({startDate, endDate}) => {
    const {onChange} = this.props;
    onChange({
      startDate: serializeDate(startDate),
      endDate: serializeDate(endDate),
    });
  };

  handleFocusChange = focused => {
    const {onFieldFocusChange} = this.props;
    this.setState({focused});
    if (onFieldFocusChange) {
      onFieldFocusChange(focused);
    }
    if (!focused) {
      const {onFocus, onBlur} = this.props;
      onFocus();
      onBlur();
    }
  };

  render() {
    const {
      disabled,
      disabledDateFields,
      minimumDays,
      disabledDate,
      initialVisibleMonth,
      readOnly,
      extraPickerProps,
    } = this.props;
    const {focused} = this.state;
    const props = {};

    if (disabledDate) {
      props.isOutsideRange = disabledDate;
    }

    return (
      <div styleName="date-period-field">
        <DateRangePicker
          {...props}
          startDate={this.getMomentValue('startDate')}
          endDate={this.getMomentValue('endDate')}
          onDatesChange={this.notifyChange}
          onFocusChange={this.handleFocusChange}
          focusedInput={focused}
          disabled={disabled || disabledDateFields || readOnly}
          inputIconPosition="before"
          minimumNights={minimumDays - 1}
          initialVisibleMonth={initialVisibleMonth}
          block
          {...extraPickerProps}
        />
      </div>
    );
  }
}

/**
 * Like `FinalField` but for a `DatePeriodField`.
 */
export function FinalDatePeriod({name, ...rest}) {
  if (rest.required) {
    rest.validate = rest.validate ? v.chain(v.dates(), rest.validate) : v.dates();
  }
  return <FinalField name={name} component={DatePeriodField} isEqual={_.isEqual} {...rest} />;
}

FinalDatePeriod.propTypes = {
  name: PropTypes.string.isRequired,
  readOnly: PropTypes.bool,
};

FinalDatePeriod.defaultProps = {
  readOnly: false,
};
