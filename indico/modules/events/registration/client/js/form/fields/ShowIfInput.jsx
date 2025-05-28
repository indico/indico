// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useForm} from 'react-final-form';
import {useSelector} from 'react-redux';

import {FinalDropdown} from 'indico/react/forms';
import {Fieldset, unsortedArraysEqual} from 'indico/react/forms/fields';
import {Translate} from 'indico/react/i18n';

import {getItems} from '../selectors';

import {getFieldRegistry} from './registry';

export function ShowIfInput({hasValueSelected}) {
  const items = Object.values(useSelector(getItems));
  const fieldRegistry = getFieldRegistry();
  const form = useForm();
  const [showValue, setShowValue] = useState(hasValueSelected);
  const [, setSelectedField] = useState(null);
  let options = [];
  const {showIfFieldId, id: thisFieldId} = form.getState().values;
  if (showValue) {
    const field = items.find(({id}) => id === showIfFieldId);
    options = fieldRegistry[field.inputType].showIfOptions(field);
    if (!options) {
      throw new Error(`Input ${field.inputType} field has no options defined`);
    }
  }
  // XXX maybe this is wrong, single choice inputs could be optional but enable some field
  // for either its options are chosen...
  const isMultipleChoice = options.length > 2;

  return (
    <Fieldset legend={Translate.string('Show if')}>
      <FinalDropdown
        name="showIfFieldId"
        label={Translate.string('Field')}
        placeholder={Translate.string('Select field...')}
        options={items
          .filter(
            ({id, inputType}) => id !== thisFieldId && !!fieldRegistry[inputType].showIfOptions
          )
          .map(({title, id: fieldId, isEnabled}) => ({
            value: fieldId,
            text: title,
            disabled: !isEnabled,
          }))}
        closeOnChange
        selection
        allowNull
        onChange={value => {
          form.change('showIfFieldValues', null);
          if (!value) {
            form.change('showIfFieldId', null);
            setSelectedField(null);
          } else {
            setSelectedField(value);
          }
          setShowValue(!!value);
        }}
      />
      {showValue && (
        <FinalDropdown
          required
          name="showIfFieldValues"
          label={Translate.string('Has values')}
          placeholder={Translate.string('Select values...')}
          options={options}
          multiple={isMultipleChoice}
          parse={value => (isMultipleChoice ? value : [value])}
          format={value => {
            if (isMultipleChoice) {
              return value ?? [];
            } else {
              return value ? value[0] : null;
            }
          }}
          isEqual={unsortedArraysEqual}
          closeOnChange
          selection
          allowNull
        />
      )}
    </Fieldset>
  );
}

ShowIfInput.propTypes = {
  hasValueSelected: PropTypes.bool,
};

ShowIfInput.defaultProps = {
  hasValueSelected: false,
};
