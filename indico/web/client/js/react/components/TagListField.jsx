// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
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

/**
 * A field that lets the user add tags or keywords
 */
function TagListField({
  value,
  disabled,
  onChange,
  onFocus,
  onBlur,
  isValid,
  searchInputProps,
  ...rest
}) {
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
      const values = newSearchQuery.split(/[,;]+/).map(v => v.trim());
      setValue([...value, ...values.filter(isValid)]);
      setSearchQuery(values.filter(a => a && !isValid(a)).join(', '));
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

  const handleAddItem = (e, {value: newItem}) => {
    if (isValid(newItem)) {
      setValue([...value, newItem]);
      setSearchQuery('');
    }
  };

  return (
    <Dropdown
      options={options}
      value={value}
      searchQuery={searchQuery}
      disabled={disabled}
      searchInput={{onFocus, onBlur, ...searchInputProps}}
      search
      selection
      multiple
      allowAdditions
      fluid
      open={isValid(searchQuery)}
      additionLabel={Translate.string('Add keyword') + ' '} // eslint-disable-line prefer-template
      onChange={handleChange}
      onSearchChange={handleSearchChange}
      onBlur={handleBlur}
      onAddItem={handleAddItem}
      selectedLabel={null}
      icon=""
      {...rest}
    />
  );
}

TagListField.propTypes = {
  value: PropTypes.arrayOf(PropTypes.string).isRequired,
  disabled: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  isValid: PropTypes.func,
  searchInputProps: PropTypes.object,
};

TagListField.defaultProps = {
  isValid: value => !!value.trim(),
  searchInputProps: {},
};

export default React.memo(TagListField);

export function FinalTagList({name, ...rest}) {
  return <FinalField name={name} component={TagListField} isEqual={_.isEqual} {...rest} />;
}

FinalTagList.propTypes = {
  name: PropTypes.string.isRequired,
};
