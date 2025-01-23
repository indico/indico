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

export function ShowIfInput({hasValueSelected}) {
  const itemsForConditionalDisplay = useSelector(state => getItemsForConditionalDisplay(state));
  const form = useForm();
  const [showValue, setShowValue] = useState(hasValueSelected);
  const [, setSelectedField] = useState(null);
  let options = [];
  const {showIfFieldId, id: thisFieldId} = form.getState().values;
  if (showValue) {
    const [{choices}] = itemsForConditionalDisplay.filter(({id}) => id === showIfFieldId);
    if (!choices) {
      options = [
        {value: '1', text: Translate.string('Yes')},
        {value: '0', text: Translate.string('No')},
      ];
    } else {
      options = choices.map(({caption, id}) => ({value: id, text: caption}));
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
          .map(({title, id: fieldId}) => ({
            value: fieldId,
            text: title,
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
