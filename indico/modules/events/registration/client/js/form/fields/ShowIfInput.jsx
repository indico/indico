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
import {Fieldset} from 'indico/react/forms/fields';
import {Translate} from 'indico/react/i18n';

import {getItemsForConditionalDisplay} from '../selectors';

import {getFieldRegistry} from './registry';

export function ShowIfInput({hasValueSelected}) {
  const itemsForConditionalDisplay = useSelector(getItemsForConditionalDisplay);
  const fieldRegistry = getFieldRegistry();
  const form = useForm();
  const [showValue, setShowValue] = useState(hasValueSelected);
  const [, setSelectedField] = useState(null);
  let options = [];
  const {showIfFieldId, id: thisFieldId} = form.getState().values;
  if (showValue) {
    const [field] = itemsForConditionalDisplay.filter(({id}) => id === showIfFieldId);
    options = fieldRegistry[field.inputType].showIfOptions(field);
    if (!options) {
      throw new Error(`Input ${field.inputType} field has no options defined`);
    }
  }

  return (
    <Fieldset legend={Translate.string('Show if')}>
      <FinalDropdown
        name="showIfFieldId"
        label={Translate.string('Field')}
        placeholder={Translate.string('Select field...')}
        options={itemsForConditionalDisplay
          .filter(({id}) => id !== thisFieldId)
          .map(({title, id: fieldId, isEnabled}) => ({
            value: fieldId,
            text: title,
            disabled: !isEnabled,
          }))}
        closeOnChange
        selection
        onChange={value => {
          form.change('showIfFieldValue', null);
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
          name="showIfFieldValue"
          label={Translate.string('Has value')}
          placeholder={Translate.string('Select value...')}
          options={options}
          closeOnChange
          selection
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
