// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {useForm} from 'react-final-form';
import {useSelector} from 'react-redux';

import {FinalDropdown} from 'indico/react/forms';
import {Fieldset} from 'indico/react/forms/fields';
import {Translate} from 'indico/react/i18n';
import PropTypes from 'indico/react/util/propTypes';

import {getItemsForConditionalDisplay} from '../selectors';

export function ShowIfInput({hasValueSelected}) {
  const itemsForConditionalDisplay = useSelector(state => getItemsForConditionalDisplay(state));
  const form = useForm();
  const [showValue, setShowValue] = useState(hasValueSelected);
  return (
    <Fieldset legend={Translate.string('Show if')}>
      <FinalDropdown
        name="showIfFieldId"
        label={Translate.string('Field')}
        placeholder={Translate.string('Select field...')}
        options={itemsForConditionalDisplay.map(({title, id: fieldId}) => ({
          value: fieldId,
          text: title,
        }))}
        closeOnChange
        selection
        onChange={value => {
          if (!value) {
            form.change('showIfFieldId', null);
            form.change('showIfFieldValue', null);
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
          // TODO: Get possible values from the field selected in showIfFieldId
          options={[
            {value: '1', text: Translate.string('Yes')},
            {value: '0', text: Translate.string('No')},
          ]}
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
