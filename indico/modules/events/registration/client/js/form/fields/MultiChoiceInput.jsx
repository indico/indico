// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
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

import {FinalCheckbox, FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../../form_setup/selectors';

import {Choices, choiceShape} from './ChoicesSetup';
import {PlacesLeft} from './PlacesLeftLabel';

import styles from '../../../styles/regform.module.scss';
import './table.module.scss';

function MultiChoiceInputComponent({value, onChange, disabled, choices, withExtraSlots}) {
  // TODO: places left
  // TODO: disable options triggering price changes after payment (or warn for managers)
  // TODO: warnings for deleted/modified choices
  const currency = useSelector(getCurrency);

  const makeHandleChange = choice => () => {
    onChange({...value, [choice.id]: +!value[choice.id]});
  };
  const makeHandleSlotsChange = choice => (__, {value: newValue}) => {
    onChange({...value, [choice.id]: +newValue});
  };

  const formatPrice = choice =>
    ((choice.extraSlotsPay ? value[choice.id] || 0 : 1) * choice.price).toFixed(2);

  return (
    <table styleName="choice-table">
      <tbody>
        {choices.map(choice => {
          return (
            <tr key={choice.id} styleName="row">
              <td>
                <Checkbox
                  styleName="checkbox"
                  value={choice.id}
                  disabled={!choice.isEnabled || disabled}
                  checked={!!value[choice.id]}
                  onChange={makeHandleChange(choice)}
                  label={choice.caption}
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
                  <PlacesLeft placesLeft={choice.placesLimit} isEnabled={choice.isEnabled} />
                )}
              </td>
              {withExtraSlots && (
                <td>
                  {choice.isEnabled && (
                    <Dropdown
                      selection
                      styleName="dropdown"
                      disabled={disabled}
                      value={value[choice.id] || 0}
                      onChange={makeHandleSlotsChange(choice)}
                      options={_.range(0, choice.maxExtraSlots + 2).map(i => ({
                        key: i,
                        value: i,
                        text: i,
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
  // TODO: placesUsed, captions - only needed once we deal with real data
};

export default function MultiChoiceInput({
  htmlName,
  disabled,
  isRequired,
  defaultValue,
  choices,
  withExtraSlots,
}) {
  return (
    <FinalField
      name={htmlName}
      component={MultiChoiceInputComponent}
      required={isRequired}
      disabled={disabled}
      fieldProps={{className: styles.field}}
      defaultValue={defaultValue}
      choices={choices}
      withExtraSlots={withExtraSlots}
    />
  );
}

MultiChoiceInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  defaultValue: PropTypes.object,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool,
};

MultiChoiceInput.defaultProps = {
  disabled: false,
  isRequired: false,
  defaultValue: {},
  withExtraSlots: false,
};

export const multiChoiceSettingsInitialData = {
  choices: [],
  withExtraSlots: false,
};

export function MultiChoiceSettings() {
  return (
    <>
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
