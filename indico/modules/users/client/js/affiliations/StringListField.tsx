// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React, {useState} from 'react';
import {Dropdown} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

function StringListField({
  value,
  disabled,
  onChange,
  onFocus,
  onBlur,
  placeholder = '',
}: {
  value: string[];
  disabled: boolean;
  onChange: (value: string[]) => void;
  onFocus: () => void;
  onBlur: () => void;
  placeholder?: string;
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const isValid = (v: string) => !!v.trim();
  const options = value.filter(isValid).map(x => ({text: x, value: x}));

  const setValue = (newValue: string[]) => {
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
    setSearchQuery(newSearchQuery);
  };

  const handleBlur = () => {
    if (isValid(searchQuery)) {
      setValue([...value, searchQuery.trim()]);
      setSearchQuery('');
    }
  };

  return (
    <Dropdown
      options={options}
      value={value}
      searchQuery={searchQuery}
      disabled={disabled}
      searchInput={{onFocus, onBlur, type: 'text'}}
      search
      selection
      multiple
      allowAdditions
      fluid
      open={!!searchQuery}
      placeholder={placeholder}
      additionLabel={Translate.string('Add') + ' '} // eslint-disable-line prefer-template
      onChange={handleChange}
      onSearchChange={handleSearchChange}
      onBlur={handleBlur}
      selectedLabel={null}
      icon=""
    />
  );
}

export default function FinalStringListField(props: {
  name: string;
  label?: string;
  placeholder?: string;
  additionLabel?: string;
  allowSeparators?: boolean;
  separators?: RegExp;
}) {
  return <FinalField component={StringListField} isEqual={_.isEqual} {...props} />;
}
