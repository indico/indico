// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Field} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Label} from 'semantic-ui-react';

import {Checkbox, Select} from 'indico/react/components';
import {FinalCheckbox, FinalField, FinalInput, validators as v} from 'indico/react/forms';
import {Translate, PluralTranslate, Param} from 'indico/react/i18n';

import {getPriceFormatter} from '../../form/selectors';
import {getFieldValue, getManagement, getPaid} from '../../form_submission/selectors';

import ChoiceLabel from './ChoiceLabel';
import {Choices, choiceShape} from './ChoicesSetup';
import {PlacesLeft} from './PlacesLeftLabel';

import '../../../styles/regform.module.scss';
import './table.module.scss';

function MultiChoiceInputComponent({
  id,
  existingValue,
  value,
  onChange,
  onFocus,
  onBlur,
  disabled,
  choices,
  withExtraSlots,
  placesUsed,
}) {
  const paid = useSelector(getPaid);
  const management = useSelector(getManagement);
  const _formatPrice = useSelector(getPriceFormatter);

  const markTouched = () => {
    onFocus();
    onBlur();
  };

  const makeHandleChange = choice => () => {
    markTouched();
    if (value[choice.id]) {
      onChange(_.omit(value, choice.id));
    } else {
      onChange({...value, [choice.id]: 1});
    }
  };
  const makeHandleSlotsChange = choice => evt => {
    markTouched();
    const selectedSlots = Number(evt.target.value);
    if (!selectedSlots) {
      onChange(_.omit(value, choice.id));
    } else {
      onChange({...value, [choice.id]: selectedSlots});
    }
  };

  const formatPrice = (choice, total = false) => {
    if (!total) {
      return _formatPrice(choice.price);
    }
    const val = value[choice.id] || 0;
    return _formatPrice((val === 0 ? 0 : choice.extraSlotsPay ? val : 1) * choice.price);
  };

  const isPaidChoice = choice => choice.price > 0 && paid;
  const isPaidChoiceLocked = choice => !management && isPaidChoice(choice);

  return (
    <table styleName="choice-table" role="presentation" id={id}>
      <tbody>
        {choices.map((choice, index) => {
          return (
            <tr key={choice.id} styleName="row">
              <td>
                <Checkbox
                  id={id ? `${id}-${index}` : ''}
                  value={choice.id}
                  disabled={
                    !choice.isEnabled ||
                    disabled ||
                    isPaidChoiceLocked(choice) ||
                    (choice.placesLimit > 0 &&
                      (placesUsed[choice.id] || 0) >= choice.placesLimit &&
                      !existingValue[choice.id])
                  }
                  checked={!!value[choice.id]}
                  onChange={makeHandleChange(choice)}
                  label={
                    <ChoiceLabel
                      choice={choice}
                      management={management}
                      paid={isPaidChoice(choice)}
                    />
                  }
                />
              </td>
              <td>
                {choice.isEnabled && !!choice.price && (
                  <Label pointing="left" styleName={!value[choice.id] ? 'greyed' : ''}>
                    {formatPrice(choice)}
                  </Label>
                )}
              </td>
              <td>
                {choice.placesLimit === 0 ? null : (
                  <PlacesLeft
                    placesLimit={choice.placesLimit}
                    placesUsed={placesUsed[choice.id] || 0}
                    isEnabled={!disabled && choice.isEnabled && !isPaidChoiceLocked(choice)}
                  />
                )}
              </td>
              {withExtraSlots && (
                <td>
                  {choice.isEnabled && (
                    <Select
                      selection
                      styleName="dropdown"
                      disabled={
                        disabled ||
                        isPaidChoiceLocked(choice) ||
                        (choice.placesLimit > 0 &&
                          (placesUsed[choice.id] || 0) - (existingValue[choice.id] || 0) >=
                            choice.placesLimit)
                      }
                      value={String(value[choice.id] || 0)}
                      onChange={makeHandleSlotsChange(choice)}
                      options={_.range(0, choice.maxExtraSlots + 2).map(i => ({
                        value: i,
                        disabled:
                          choice.placesLimit > 0 &&
                          (placesUsed[choice.id] || 0) - (existingValue[choice.id] || 0) + i >
                            choice.placesLimit,
                      }))}
                      required
                    />
                  )}
                </td>
              )}
              {withExtraSlots && (
                <td>
                  {choice.isEnabled && !!choice.price && !!value[choice.id] && (
                    <Label pointing="left">
                      <Translate>
                        Total: <Param name="price" value={formatPrice(choice, true)} />
                      </Translate>
                    </Label>
                  )}
                </td>
              )}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

MultiChoiceInputComponent.propTypes = {
  id: PropTypes.string.isRequired,
  value: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  onFocus: PropTypes.func.isRequired,
  onBlur: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool.isRequired,
  placesUsed: PropTypes.objectOf(PropTypes.number).isRequired,
  existingValue: PropTypes.objectOf(PropTypes.number).isRequired,
};

export default function MultiChoiceInput({
  fieldId,
  htmlId,
  htmlName,
  disabled,
  isRequired,
  choices,
  maxChoices,
  withExtraSlots,
  placesUsed,
}) {
  const existingValue = useSelector(state => getFieldValue(state, fieldId)) || {};
  return (
    <FinalField
      id={htmlId}
      name={htmlName}
      component={MultiChoiceInputComponent}
      required={isRequired ? 'no-validator' : false}
      disabled={disabled}
      choices={choices}
      withExtraSlots={withExtraSlots}
      placesUsed={placesUsed}
      existingValue={existingValue}
      isEqual={_.isEqual}
      validate={value => {
        if (isRequired && !_.keys(value).length) {
          return Translate.string('This field is required');
        }
        if (maxChoices && _.keys(value).length > maxChoices) {
          return PluralTranslate.string(
            'At most {n} option can be selected',
            'At most {n} options can be selected',
            maxChoices,
            {n: maxChoices}
          );
        }
      }}
    />
  );
}

MultiChoiceInput.propTypes = {
  fieldId: PropTypes.number.isRequired,
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  maxChoices: PropTypes.number,
  withExtraSlots: PropTypes.bool,
  placesUsed: PropTypes.objectOf(PropTypes.number).isRequired,
};

MultiChoiceInput.defaultProps = {
  disabled: false,
  isRequired: false,
  maxChoices: null,
  withExtraSlots: false,
};

export const multiChoiceSettingsInitialData = {
  choices: [],
  withExtraSlots: false,
};

export function MultiChoiceSettings() {
  return (
    <>
      <Field name="choices" subscription={{value: true}}>
        {({input: {value}}) => {
          const min = value.length > 0 ? 1 : 0;
          const max = value.length > 0 ? value.length : 0;
          return (
            <FinalInput
              name="maxChoices"
              type="number"
              placeholder={Translate.string('Unlimited', 'Number of choices')}
              step="1"
              min={min}
              max={max}
              validate={v.optional(v.range(min, max))}
              label={Translate.string('Maximum number of choices')}
              description={Translate.string(
                'Maximum number of choices that can be selected. Leave empty to unset.'
              )}
            />
          );
        }}
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

export function multiChoiceShowIfOptions(field) {
  return field.choices.map(({caption, id}) => ({value: id, text: caption}));
}

export function multiChoiceGetDataForCondition(value) {
  return Object.entries(value)
    .filter(([, slots]) => slots > 0)
    .map(([key]) => key);
}
