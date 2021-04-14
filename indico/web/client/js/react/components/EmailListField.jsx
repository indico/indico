// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Dropdown} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {FinalField} from '../forms';

const isValid = value => /^\S+@\S+\.\S+$/.test(value);

/**
 * A field that lets the user enter email addresses
 */
const EmailListField = props => {
  const {value, disabled, onChange, onFocus, onBlur} = props;
  const [options, setOptions] = useState(value.filter(isValid).map(x => ({text: x, value: x})));

  const handleChange = (e, {value: newValue}) => {
    newValue = _.uniq(newValue.filter(isValid));
    setOptions(newValue.map(x => ({text: x, value: x})));
    onChange(newValue);
    onFocus();
    onBlur();
  };

  return (
    <Dropdown
      options={options}
      value={value}
      disabled={disabled}
      searchInput={{onFocus, onBlur, type: 'email'}}
      search
      selection
      multiple
      allowAdditions
      fluid
      closeOnChange
      noResultsMessage={Translate.string('Please enter an email address')}
      placeholder={Translate.string('Please enter an email address')}
      additionLabel={Translate.string('Add email') + ' '} // eslint-disable-line prefer-template
      onChange={handleChange}
    />
  );
};

EmailListField.propTypes = {
  value: PropTypes.arrayOf(PropTypes.string).isRequired,
  disabled: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
};

export default React.memo(EmailListField);

/**
 * Like `FinalField` but for a `EmailListField`.
 */
export function FinalEmailList({name, ...rest}) {
  return <FinalField name={name} component={EmailListField} isEqual={_.isEqual} {...rest} />;
}

FinalEmailList.propTypes = {
  name: PropTypes.string.isRequired,
};
