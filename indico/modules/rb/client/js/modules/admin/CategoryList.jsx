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

const isValid = value => +value >= 0;

// TODO: make this nicer (searching by title/id, showing titles instead of IDs)

/**
 * A field that lets the user enter category IDs.
 */
const CategoryList = props => {
  const {value, disabled, onChange, onFocus, onBlur} = props;
  const [options, setOptions] = useState(value.filter(isValid).map(x => ({text: x, value: x})));

  const handleChange = (e, {value: newValue}) => {
    newValue = _.uniq(newValue.filter(isValid).map(x => +x));
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
      searchInput={{onFocus, onBlur, pattern: '^\\d+$'}}
      search
      selection
      multiple
      allowAdditions
      fluid
      closeOnChange
      noResultsMessage={Translate.string('Please enter a category ID')}
      placeholder={Translate.string('Please enter a category ID')}
      additionLabel={Translate.string('Add category') + ' #'} // eslint-disable-line prefer-template
      onChange={handleChange}
    />
  );
};

CategoryList.propTypes = {
  value: PropTypes.arrayOf(PropTypes.number).isRequired,
  disabled: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
};

export default React.memo(CategoryList);
