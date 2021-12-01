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
import {Checkbox, Form, Dropdown, Label} from 'semantic-ui-react';

import {FinalCheckbox, FinalField} from 'indico/react/forms';
import {Translate, PluralTranslate, Singular, Plural, Param} from 'indico/react/i18n';

import {getCurrency} from '../../form_setup/selectors';

import {Choices, choiceShape} from './ChoicesSetup';

import '../../../styles/regform.module.scss';

function PlacesLeft({placesLeft, isEnabled}) {
  const color = placesLeft > 0 ? (isEnabled ? 'green' : 'grey') : 'red';

  return (
    <Label color={color} style={{whiteSpace: 'nowrap'}}>
      {placesLeft > 0 ? (
        <PluralTranslate count={placesLeft}>
          <Singular>1 place left</Singular>
          <Plural>
            <Param name="count" value={placesLeft} /> places left
          </Plural>
        </PluralTranslate>
      ) : (
        <Translate>No places left</Translate>
      )}
    </Label>
  );
}

PlacesLeft.propTypes = {
  placesLeft: PropTypes.number.isRequired,
  isEnabled: PropTypes.bool.isRequired,
};

export default function MultiChoiceInput({
  htmlName,
  disabled,
  choices,
  withExtraSlots,
  title,
  isRequired,
}) {
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

  const noPrices = choices.every(choice => choice.price === 0);

  return (
    <Form.Field required={isRequired} styleName="field">
      <label>{title}</label>
      <table styleName="multichoice-table">
        <tbody>
          {choices.map(choice => {
            return (
              <tr key={choice.id}>
                <td style={{paddingTop: 10, paddingBottom: 10}}>
                  <Checkbox
                    styleName="multichoice-checkbox"
                    name={htmlName}
                    value={choice.id}
                    disabled={!choice.isEnabled || disabled || choice.placesLimit === 0}
                    checked={!!value[choice.id]}
                    onChange={makeHandleChange(choice)}
                    label={choice.caption}
                  />
                </td>
                {!withExtraSlots && !noPrices && (
                  <td style={{paddingLeft: 5}}>
                    {choice.isEnabled && choice.placesLimit > 0 && (
                      <Label pointing="left">
                        {choice.price.toFixed(2)} {currency}
                      </Label>
                    )}
                  </td>
                )}
                {withExtraSlots && (
                  <td style={{paddingLeft: 5}}>
                    {choice.isEnabled && choice.placesLimit > 0 && (
                      <Dropdown
                        selection
                        styleName="multichoice-dropdown"
                        name={`${htmlName}-${choice.id}-extra`}
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
                {withExtraSlots && !noPrices && (
                  <td style={{paddingLeft: 5}}>
                    {choice.isEnabled && choice.placesLimit > 0 && (
                      <Label pointing="left">
                        {choice.price.toFixed(2)} {currency} (Total: {formatPrice(choice)}{' '}
                        {currency})
                      </Label>
                    )}
                  </td>
                )}
                <td style={{paddingLeft: 5}}>
                  <PlacesLeft placesLeft={choice.placesLimit} isEnabled={choice.isEnabled} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Form.Field>
  );
}

MultiChoiceInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  choices: PropTypes.arrayOf(PropTypes.shape(choiceShape)).isRequired,
  withExtraSlots: PropTypes.bool,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
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
