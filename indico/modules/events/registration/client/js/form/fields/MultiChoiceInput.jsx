// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Field} from 'react-final-form';
import {useSelector} from 'react-redux';
import {Checkbox, Dropdown, Label} from 'semantic-ui-react';

import {FinalCheckbox, FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../../form_setup/selectors';

import {Choices, choiceShape} from './ChoicesSetup';
import {PlacesLeft} from './PlacesLeftLabel';

import '../../../styles/regform.module.scss';
import './table.module.scss';

export default function MultiChoiceInput({htmlName, disabled, choices, withExtraSlots}) {
  // TODO: billable/price
  // TODO: places left
  // TODO: set value as `{uuid: places}` (when adding final-form integration)
  // TODO: disable options triggering price changes after payment (or warn for managers)
  // TODO: warnings for deleted/modified choices
  const currency = useSelector(getCurrency);
  const [value, setValue] = useState({});

  const makeHandleChange = choice => () => {
    setValue(prev => ({...prev, [choice.id]: +!prev[choice.id]}));
  };
  const makeHandleSlotsChange = choice => (__, {value: newValue}) => {
    setValue(prev => ({...prev, [choice.id]: +newValue}));
  };

  const formatPrice = choice =>
    ((choice.extraSlotsPay ? value[choice.id] || 0 : 1) * choice.price).toFixed(2);

  return (
    <table>
      <tbody>
        {choices.map(choice => {
          return (
            <tr key={choice.id} styleName="row">
              <td>
                <Checkbox
                  styleName="checkbox"
                  name={htmlName}
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

MultiChoiceInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool,
  // TODO: placesUsed, captions - only needed once we deal with real data
};

MultiChoiceInput.defaultProps = {
  disabled: false,
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
