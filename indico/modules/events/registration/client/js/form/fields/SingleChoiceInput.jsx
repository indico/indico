// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createDecorator from 'final-form-calculate';
import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Field} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Form, Label, Dropdown} from 'semantic-ui-react';

import {FinalCheckbox, FinalDropdown, FinalField, parsers as p} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../../form_setup/selectors';

import {Choices, choiceShape} from './ChoicesSetup';
import {PlacesLeft} from './PlacesLeftLabel';

import styles from '../../../styles/regform.module.scss';
import './table.module.scss';

function SingleChoiceDropdown({value, onChange, disabled, isRequired, choices, withExtraSlots}) {
  const currency = useSelector(getCurrency);
  const selectedChoice = choices.find(c => Object.prototype.hasOwnProperty.call(value, c.id)) || {};

  let extraSlotsDropdown = null;
  if (withExtraSlots && selectedChoice && selectedChoice.maxExtraSlots > 0) {
    const options = _.range(1, selectedChoice.maxExtraSlots + 2).map(i => ({
      key: i,
      value: i,
      text: i,
    }));
    extraSlotsDropdown = (
      <Form.Select
        options={options}
        disabled={disabled}
        value={value[selectedChoice.id]}
        onChange={(_evt, data) => onChange({[selectedChoice.id]: data.value})}
        fluid
      />
    );
  }

  const options = choices.map(c => ({
    key: c.id,
    value: c.id,
    disabled: !c.isEnabled,
    text: (
      <div styleName="dropdown-text">
        <div styleName="caption">{c.caption}</div>
        <div styleName="labels">
          {!!c.price && (
            <Label>
              {c.price} {currency}
            </Label>
          )}
          {c.placesLimit === 0 ? null : (
            <PlacesLeft placesLeft={c.placesLimit} isEnabled={c.isEnabled} />
          )}
        </div>
      </div>
    ),
  }));

  return (
    <Form.Group styleName="single-choice-dropdown">
      <Form.Select
        style={{width: 500}}
        placeholder={Translate.string('Choose an option')}
        options={options}
        disabled={disabled}
        value={selectedChoice.id}
        onChange={(e, data) => onChange({[data.value]: 1})}
        clearable={!isRequired}
        search
      />
      {extraSlotsDropdown}
      {extraSlotsDropdown && !!selectedChoice.price && (
        <Label pointing="left">
          {Translate.string('Total: {total} {currency}', {
            total: (
              (selectedChoice.extraSlotsPay ? value[selectedChoice.id] : 1) * selectedChoice.price
            ).toFixed(2),
            currency,
          })}
        </Label>
      )}
    </Form.Group>
  );
}

SingleChoiceDropdown.propTypes = {
  value: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  isRequired: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool.isRequired,
};

function SingleChoiceRadioGroup({value, onChange, disabled, isRequired, choices, withExtraSlots}) {
  const currency = useSelector(getCurrency);
  const selectedChoice = choices.find(c => Object.prototype.hasOwnProperty.call(value, c.id)) || {};
  const radioChoices = [...choices];
  if (!isRequired) {
    radioChoices.unshift({id: '', isEnabled: true, caption: Translate.string('None')});
  }

  const handleChange = newValue => {
    if (newValue === '') {
      onChange({});
    } else {
      onChange({[newValue]: 1});
    }
  };

  const isChecked = (currentChoice, idx) =>
    currentChoice.id === selectedChoice.id || (idx === 0 && !selectedChoice.id);

  return (
    <table styleName="choice-table">
      <tbody>
        {radioChoices.map((c, idx) => {
          return (
            <tr key={c.id} styleName="row">
              <td>
                <Form.Radio
                  styleName="radio"
                  label={c.caption}
                  key={c.id}
                  value={c.id}
                  disabled={!c.isEnabled || disabled}
                  checked={isChecked(c, idx)}
                  onChange={() => handleChange(c.id)}
                />
              </td>
              <td>
                {c.isEnabled && !!c.price && (
                  <Label pointing="left">
                    {c.price.toFixed(2)} {currency}
                  </Label>
                )}
              </td>
              <td>
                {c.id !== '' && c.placesLimit !== 0 && (
                  <PlacesLeft placesLeft={c.placesLimit} isEnabled={c.isEnabled} />
                )}
              </td>
              {withExtraSlots && !!c.maxExtraSlots && selectedChoice.id === c.id && (
                <>
                  <td>
                    {c.isEnabled && (
                      <Dropdown
                        selection
                        styleName="dropdown"
                        value={value[selectedChoice.id]}
                        onChange={(e, data) => onChange({[selectedChoice.id]: data.value})}
                        options={_.range(1, c.maxExtraSlots + 2).map(i => ({
                          key: i,
                          value: i,
                          text: i,
                        }))}
                      />
                    )}
                  </td>
                  <td>
                    {c.isEnabled && !!c.price && (
                      <Label pointing="left">
                        {Translate.string('Total: {total} {currency}', {
                          total: (value[selectedChoice.id] * c.price).toFixed(2),
                          currency,
                        })}
                      </Label>
                    )}
                  </td>
                </>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

SingleChoiceRadioGroup.propTypes = {
  value: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  isRequired: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool.isRequired,
};

function SingleChoiceInputComponent({
  value,
  onChange,
  disabled,
  isRequired,
  itemType,
  choices,
  withExtraSlots,
}) {
  // TODO: disable options triggering price changes after payment (or warn for managers)
  // TODO: warnings for deleted/modified choices

  let component = null;
  if (itemType === 'dropdown') {
    component = (
      <SingleChoiceDropdown
        value={value}
        onChange={onChange}
        disabled={disabled}
        isRequired={isRequired}
        choices={choices}
        withExtraSlots={withExtraSlots}
      />
    );
  } else if (itemType === 'radiogroup') {
    component = (
      <SingleChoiceRadioGroup
        value={value}
        onChange={onChange}
        disabled={disabled}
        isRequired={isRequired}
        choices={choices}
        withExtraSlots={withExtraSlots}
      />
    );
  } else {
    return `ERROR: Unknown type ${itemType}`;
  }

  return component;
}

SingleChoiceInputComponent.propTypes = {
  disabled: PropTypes.bool.isRequired,
  isRequired: PropTypes.bool.isRequired,
  itemType: PropTypes.oneOf(['dropdown', 'radiogroup']).isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool.isRequired,
  // TODO: placesUsed, captions - only needed once we deal with real data
};

export default function SingleChoiceInput({
  htmlName,
  disabled,
  isRequired,
  defaultValue,
  itemType,
  choices,
  withExtraSlots,
}) {
  return (
    <FinalField
      name={htmlName}
      component={SingleChoiceInputComponent}
      required={isRequired}
      isRequired={isRequired}
      disabled={disabled}
      fieldProps={{className: styles.field}}
      defaultValue={defaultValue}
      itemType={itemType}
      choices={choices}
      withExtraSlots={withExtraSlots}
    />
  );
}

SingleChoiceInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  defaultValue: PropTypes.object,
  itemType: PropTypes.oneOf(['dropdown', 'radiogroup']).isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool,
};

SingleChoiceInput.defaultProps = {
  disabled: false,
  isRequired: false,
  defaultValue: {},
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
