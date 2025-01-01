// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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
  const [searchQuery, setSearchQuery] = useState('');
  const options = value.filter(isValid).map(x => ({text: x, value: x}));

  const setValue = newValue => {
    newValue = _.uniq(newValue.filter(isValid));
    onChange(newValue);
    onFocus();
    onBlur();
  };

  const handleChange = (e, {value: newValue}) => {
    if (newValue.length && newValue[newValue.length - 1] === searchQuery) {
      setSearchQuery('');
    }
    setValue(newValue);
  };

  const handleSearchChange = (e, {searchQuery: newSearchQuery}) => {
    if (/[,;]/.test(newSearchQuery)) {
      const addresses = newSearchQuery.replace(/\s/g, '').split(/[,;]+/);
      setValue([...value, ...addresses.filter(isValid)]);
      setSearchQuery(addresses.filter(a => a && !isValid(a)).join(', '));
    } else {
      setSearchQuery(newSearchQuery);
    }
  };

  const handleBlur = () => {
    if (isValid(searchQuery)) {
      setValue([...value, searchQuery]);
      setSearchQuery('');
    }
  };

  return (
    <Dropdown
      options={options}
      value={value}
      searchQuery={searchQuery}
      disabled={disabled}
      searchInput={{onFocus, onBlur, type: 'email'}}
      search
      selection
      multiple
      allowAdditions
      fluid
      open={isValid(searchQuery)}
      placeholder={Translate.string('Please enter an email address')}
      additionLabel={Translate.string('Add email') + ' '} // eslint-disable-line prefer-template
      onChange={handleChange}
      onSearchChange={handleSearchChange}
      onBlur={handleBlur}
      selectedLabel={null}
      icon=""
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
