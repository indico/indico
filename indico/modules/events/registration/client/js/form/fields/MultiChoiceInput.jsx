// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import {Field} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Checkbox, Dropdown, Label} from 'semantic-ui-react';

import {FinalCheckbox, FinalField, FinalInput, validators as v} from 'indico/react/forms';
import {Translate, PluralTranslate} from 'indico/react/i18n';

import {getCurrency} from '../../form/selectors';
import {getFieldValue, getManagement, getPaid} from '../../form_submission/selectors';

import ChoiceLabel from './ChoiceLabel';
import {Choices, choiceShape} from './ChoicesSetup';
import {PlacesLeft} from './PlacesLeftLabel';

import '../../../styles/regform.module.scss';
import './table.module.scss';

function MultiChoiceInputComponent({
  existingValue,
  value,
  onChange,
  disabled,
  choices,
  withExtraSlots,
  placesUsed,
}) {
  const paid = useSelector(getPaid);
  const management = useSelector(getManagement);
  const currency = useSelector(getCurrency);

  const makeHandleChange = choice => () => {
    if (value[choice.id]) {
      onChange(_.omit(value, choice.id));
    } else {
      onChange({...value, [choice.id]: +!value[choice.id]});
    }
  };
  const makeHandleSlotsChange = choice => (__, {value: newValue}) => {
    if (!+newValue) {
      onChange(_.omit(value, choice.id));
    } else {
      onChange({...value, [choice.id]: +newValue});
    }
  };

  const formatPrice = choice => {
    const val = value[choice.id] || 0;
    return ((val === 0 ? 0 : choice.extraSlotsPay ? val : 1) * choice.price).toFixed(2);
  };

  const isPaidChoice = choice => choice.price > 0 && paid;
  const isPaidChoiceLocked = choice => !management && isPaidChoice(choice);

  return (
    <table styleName="choice-table">
      <tbody>
        {choices.map(choice => {
          return (
            <tr key={choice.id} styleName="row">
              <td>
                <Checkbox
                  styleName="checkbox"
                  style={{pointerEvents: 'auto'}} // keep label tooltips working when disabled
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
                  label={{
                    children: (
                      <ChoiceLabel
                        choice={choice}
                        management={management}
                        paid={isPaidChoice(choice)}
                      />
                    ),
                  }}
                />
              </td>
              <td>
                {choice.isEnabled && !!choice.price && (
                  <Label pointing="left">
                    {choice.price.toFixed(2)} {currency}
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
                    <Dropdown
                      selection
                      styleName="dropdown"
                      disabled={
                        disabled ||
                        isPaidChoiceLocked(choice) ||
                        (choice.placesLimit > 0 &&
                          (placesUsed[choice.id] || 0) - (existingValue[choice.id] || 0) >=
                            choice.placesLimit)
                      }
                      value={value[choice.id] || 0}
                      onChange={makeHandleSlotsChange(choice)}
                      options={_.range(0, choice.maxExtraSlots + 2).map(i => ({
                        key: i,
                        value: i,
                        text: i,
                        disabled:
                          choice.placesLimit > 0 &&
                          (placesUsed[choice.id] || 0) - (existingValue[choice.id] || 0) + i >
                            choice.placesLimit,
                      }))}
                    />
                  )}
                </td>
              )}
              {withExtraSlots && (
                <td>
                  {choice.isEnabled && !!choice.price && (
                    <Label pointing="left">
                      {Translate.string('Total: {total} {currency}', {
                        total: formatPrice(choice),
                        currency,
                      })}
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
  value: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool.isRequired,
  placesUsed: PropTypes.objectOf(PropTypes.number).isRequired,
  existingValue: PropTypes.objectOf(PropTypes.number).isRequired,
};

export default function MultiChoiceInput({
  id,
  htmlName,
  disabled,
  isRequired,
  choices,
  maxChoices,
  withExtraSlots,
  placesUsed,
}) {
  const existingValue = useSelector(state => getFieldValue(state, id)) || {};
  return (
    <FinalField
      name={htmlName}
      component={MultiChoiceInputComponent}
      required={isRequired}
      disabled={disabled}
      choices={choices}
      withExtraSlots={withExtraSlots}
      placesUsed={placesUsed}
      existingValue={existingValue}
      isEqual={_.isEqual}
      validate={value => {
        if (maxChoices && _.keys(value).length > maxChoices) {
          return PluralTranslate.string(
            'At most one option can be selected',
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
  id: PropTypes.number.isRequired,
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
