// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React, {useMemo, useState} from 'react';
import {Dropdown, DropdownProps} from 'semantic-ui-react';

import {FinalField} from 'indico/react/forms';

interface StringListFieldProps {
  value: string[];
  disabled: boolean;
  onChange: (value: string[]) => void;
  onFocus: () => void;
  onBlur: () => void;
  placeholder?: string;
  additionLabel?: string;
  allowSeparators?: boolean;
  separators?: RegExp;
}

export function StringListField({
  value,
  disabled,
  onChange,
  onBlur,
  onFocus,
  placeholder,
  additionLabel,
  allowSeparators = false,
  separators = /[,;]+/,
}: StringListFieldProps): JSX.Element {
  const [searchQuery, setSearchQuery] = useState('');
  const options = useMemo(() => value.map(text => ({text, value: text})), [value]);

  const setValue = (newValues: string[]) => {
    const deduped = _.uniq(newValues.filter(Boolean));
    onChange(deduped);
    onFocus();
    onBlur();
  };

  const handleChange: NonNullable<DropdownProps['onChange']> = (event, {value: newValue}) => {
    const values = Array.isArray(newValue) ? (newValue.filter(x => x) as string[]) : [];
    if (values.length && values[values.length - 1] === searchQuery) {
      setSearchQuery('');
    }
    setValue(values);
  };

  const handleSearchChange: NonNullable<DropdownProps['onSearchChange']> = (
    event,
    {searchQuery: newSearchQuery}
  ) => {
    if (allowSeparators && separators.test(newSearchQuery)) {
      const entries = newSearchQuery.split(separators).map(part => part.trim());
      setValue([...value, ...entries.filter(Boolean)]);
      setSearchQuery(entries.filter(part => part && !value.includes(part)).join(', '));
    } else {
      setSearchQuery(newSearchQuery);
    }
  };

  const handleBlur = () => {
    const trimmed = searchQuery.trim();
    if (trimmed) {
      setValue([...value, trimmed]);
      setSearchQuery('');
    }
  };

  return (
    <Dropdown
      options={options}
      value={value}
      search
      multiple
      selection
      allowAdditions
      fluid
      searchQuery={searchQuery}
      placeholder={placeholder}
      additionLabel={additionLabel}
      disabled={disabled}
      icon=""
      onChange={handleChange}
      onSearchChange={handleSearchChange}
      onBlur={handleBlur}
      searchInput={{onFocus, onBlur: handleBlur}}
      selectedLabel={null}
      closeOnChange
    />
  );
}

interface FinalStringListFieldProps {
  name: string;
  label?: string;
  placeholder?: string;
  additionLabel?: string;
  allowSeparators?: boolean;
  separators?: RegExp;
}

export function FinalStringListField(props: FinalStringListFieldProps): JSX.Element {
  return (
    <FinalField
      component={StringListField}
      isEqual={_.isEqual}
      parse={value => value || []}
      format={value => value || []}
      {...props}
    />
  );
}
