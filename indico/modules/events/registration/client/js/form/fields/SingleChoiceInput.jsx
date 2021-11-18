// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createDecorator from 'final-form-calculate';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Field} from 'react-final-form';

import {FinalCheckbox, FinalDropdown, FinalField, parsers as p} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {Choices, choiceShape} from './ChoicesSetup';

import '../../../styles/regform.module.scss';

function SingleChoiceDropdown({htmlName, disabled, choices, value, onChange}) {
  return (
    <select name={htmlName} disabled={disabled} value={value} onChange={onChange}>
      <option key="" value="">
        {Translate.string('Choose an option')}
      </option>
      {choices.map(c => (
        <option key={c.id} value={c.id} disabled={!c.isEnabled}>
          {c.caption}
        </option>
      ))}
    </select>
  );
}

SingleChoiceDropdown.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

function SingleChoiceRadioGroup({htmlName, disabled, choices, value, onChange, isRequired}) {
  const radioChoices = [...choices];
  if (!isRequired) {
    radioChoices.unshift({id: '', isEnabled: true, caption: Translate.string('None')});
  }
  return (
    <ul styleName="radio-group">
      {radioChoices.map(c => (
        <li key={c.id}>
          <input
            type="radio"
            name={htmlName}
            id={`${htmlName}-${c.id}`}
            value={c.id}
            disabled={!c.isEnabled || disabled}
            checked={c.id === value}
            onChange={onChange}
          />{' '}
          <label htmlFor={`${htmlName}-${c.id}`}>{c.caption}</label>
        </li>
      ))}
    </ul>
  );
}

SingleChoiceRadioGroup.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  isRequired: PropTypes.bool.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default function SingleChoiceInput({
  htmlName,
  disabled,
  isRequired,
  itemType,
  choices,
  defaultItem,
  withExtraSlots,
}) {
  // TODO: billable/price
  // TODO: places left
  // TODO: set value as `{uuid: places}` (when adding final-form integration)
  // TODO: disable options triggering price changes after payment (or warn for managers)
  // TODO: warnings for deleted/modified choices
  const [value, setValue] = useState(defaultItem || '');
  const [slotsUsed, setSlotsUsed] = useState(1);
  const selectedChoice = choices.find(c => c.id === value);

  let extraSlotsDropdown = null;
  if (withExtraSlots && selectedChoice && selectedChoice.maxExtraSlots > 0) {
    extraSlotsDropdown = (
      <select
        name={`${htmlName}-extra`}
        disabled={disabled}
        value={slotsUsed}
        onChange={evt => setSlotsUsed(evt.target.value)}
      >
        {_.range(1, selectedChoice.maxExtraSlots + 2).map(i => (
          <option key={i} value={i}>
            {i}
          </option>
        ))}
      </select>
    );
  }

  const handleChange = evt => {
    setValue(evt.target.value);
    setSlotsUsed(1);
  };

  let component = null;
  if (itemType === 'dropdown') {
    component = (
      <SingleChoiceDropdown
        htmlName={htmlName}
        disabled={disabled}
        choices={choices}
        extraSlotsDropdown={extraSlotsDropdown}
        value={value}
        onChange={handleChange}
      />
    );
  } else if (itemType === 'radiogroup') {
    component = (
      <SingleChoiceRadioGroup
        htmlName={htmlName}
        disabled={disabled}
        choices={choices}
        extraSlotsDropdown={extraSlotsDropdown}
        value={value}
        onChange={handleChange}
        isRequired={isRequired}
      />
    );
  } else {
    return `ERROR: Unknown type ${itemType}`;
  }

  return (
    <>
      {component}
      {extraSlotsDropdown}
    </>
  );
}

SingleChoiceInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  itemType: PropTypes.oneOf(['dropdown', 'radiogroup']).isRequired,
  defaultItem: PropTypes.string,
  isRequired: PropTypes.bool.isRequired,
  withExtraSlots: PropTypes.bool,
  // TODO: placesUsed, captions - only needed once we deal with real data
};

SingleChoiceInput.defaultProps = {
  disabled: false,
  defaultItem: null,
  withExtraSlots: false,
};

export const singleChoiceSettingsFormDecorator = createDecorator({
  field: 'choices',
  updates: (choices, __, {defaultItem}) => {
    // clear the default item when it's removed from the choices or disabled
    if (!choices.some(c => c.id === defaultItem && c.isEnabled)) {
      return {defaultItem: null};
    }
    return {};
  },
});

export const singleChoiceSettingsInitialData = {
  choices: [],
  itemType: 'dropdown',
  defaultItem: null,
  withExtraSlots: false,
};

export function SingleChoiceSettings() {
  return (
    <>
      <FinalDropdown
        name="itemType"
        label={Translate.string('Widget type')}
        options={[
          {key: 'dropdown', value: 'dropdown', text: Translate.string('Drop-down list')},
          {key: 'radiogroup', value: 'radiogroup', text: Translate.string('Radio buttons')},
        ]}
        selection
        required
      />
      <Field name="choices" subscription={{value: true}} isEqual={_.isEqual}>
        {({input: {value: choices}}) => (
          <FinalDropdown
            name="defaultItem"
            label={Translate.string('Default option')}
            options={choices
              .filter(c => c.isEnabled)
              .map(c => ({key: c.id, value: c.id, text: c.caption}))}
            disabled={!choices.some(c => c.isEnabled)}
            parse={p.nullIfEmpty}
            selection
          />
        )}
      </Field>
      <FinalCheckbox name="withExtraSlots" label={Translate.string('Enable extra slots')} />
      <Field name="withExtraSlots" subscription={{value: true}}>
        {({input: {value: withExtraSlots}}) => (
          <FinalField
            name="choices"
            label={Translate.string('Choices')}
            component={Choices}
            withExtraSlots={withExtraSlots}
            isEqual={_.isEqual}
            required
          />
        )}
      </Field>
    </>
  );
}
