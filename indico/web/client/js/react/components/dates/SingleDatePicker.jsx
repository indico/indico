// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'react-dates/initialize';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {SingleDatePicker as ReactDatesSinglePicker} from 'react-dates';
import {serializeDate, toMoment} from 'indico/utils/date';
import {FinalField} from 'indico/react/forms';
import {responsiveReactDates} from './util';

import 'react-dates/lib/css/_datepicker.css';
import '../style/dates.scss';

const PROP_BLACKLIST = new Set([
  'name',
  'value',
  'onBlur',
  'onChange',
  'onFocus',
  'label',
  'disabledDate',
  'render',
]);

export default class SingleDatePicker extends React.Component {
  static propTypes = {
    disabledDate: PropTypes.func,
  };

  static defaultProps = {
    disabledDate: null,
  };

  state = {
    focused: false,
  };

  onFocusChange = ({focused}) => {
    this.setState({focused});
  };

  render() {
    const {focused} = this.state;
    const {disabledDate} = this.props;
    const filteredProps = Object.entries(this.props)
      .filter(([name]) => {
        return !PROP_BLACKLIST.has(name);
      })
      .reduce((acc, curr) => {
        const [key, value] = curr;
        return {...acc, [key]: value};
      }, {});

    if (disabledDate) {
      filteredProps.isOutsideRange = disabledDate;
    }

    return responsiveReactDates(ReactDatesSinglePicker, {
      onFocusChange: this.onFocusChange,
      inputIconPosition: 'after',
      numberOfMonths: 1,
      hideKeyboardShortcutsPanel: true,
      showDefaultInputIcon: true,
      focused,
      ...filteredProps,
    });
  }
}

function ValuedSingleDatePicker({value, onChange, asRange, ...rest}) {
  const date = toMoment(asRange ? value.startDate : value, 'YYYY-MM-DD');
  const handleDateChange = newDate => {
    if (asRange) {
      onChange({
        startDate: serializeDate(newDate),
        endDate: null,
      });
    } else {
      onChange(serializeDate(newDate));
    }
  };
  return <SingleDatePicker date={date} onDateChange={handleDateChange} {...rest} />;
}

ValuedSingleDatePicker.propTypes = {
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.shape({
      startDate: PropTypes.string.isRequired,
      // endDate: null  -- not supported by propTypes :(
    }),
  ]).isRequired,
  asRange: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
};

ValuedSingleDatePicker.defaultProps = {
  asRange: false,
};

/**
 * Like `FinalField` but for a `SingleDatePicker`.
 */
export function FinalSingleDatePicker({name, ...rest}) {
  return (
    <FinalField name={name} component={ValuedSingleDatePicker} isEqual={_.isEqual} {...rest} />
  );
}

FinalSingleDatePicker.propTypes = {
  name: PropTypes.string.isRequired,
};
