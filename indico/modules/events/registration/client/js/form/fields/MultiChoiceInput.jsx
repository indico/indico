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
    ((choice.extraSlotsPay ? value[choice.id] : 1) * choice.price).toFixed(1);

  const selected = Object.values(value).some(v => v !== 0);

  return (
    <Form.Field required={isRequired} styleName="field">
      <label>{title}</label>
      <table styleName="multichoice-table">
        <tbody>
          {choices.map(choice => {
            return (
              <tr key={choice.id}>
                <td style={{paddingRight: 20}}>
                  <div style={{maxWidth: 320}}>
                    <Checkbox
                      name={htmlName}
                      value={choice.id}
                      disabled={!choice.isEnabled || disabled || choice.placesLimit === 0}
                      checked={!!value[choice.id]}
                      onChange={makeHandleChange(choice)}
                      label={
                        choice.caption +
                        (!withExtraSlots && choice.price ? ` (${choice.price} ${currency})` : '')
                      }
                    />
                  </div>
                </td>
                <td style={{paddingRight: 40}}>
                  {choice.placesLimit > 0 ? (
                    <Label color="green">
                      <span style={{whiteSpace: 'nowrap'}}>
                        <PluralTranslate count={choice.placesLimit}>
                          <Singular>1 space left</Singular>
                          <Plural>
                            <Param name="count" value={choice.placesLimit} /> spaces left
                          </Plural>
                        </PluralTranslate>
                      </span>
                    </Label>
                  ) : (
                    <Label color="red">
                      <span style={{whiteSpace: 'nowrap'}}>
                        <Translate>No places left</Translate>
                      </span>
                    </Label>
                  )}
                </td>
                {withExtraSlots && selected && (
                  <td style={{paddingRight: 20}}>
                    {!!value[choice.id] && (
                      <Dropdown
                        selection
                        style={{minWidth: 80}}
                        disabled={choice.maxExtraSlots === 0}
                        name={`${htmlName}-${choice.id}-extra`}
                        value={value[choice.id]}
                        onChange={makeHandleSlotsChange(choice)}
                        options={_.range(1, choice.maxExtraSlots + 2).map(i => ({
                          key: i,
                          value: i,
                          text: i,
                        }))}
                      />
                    )}
                  </td>
                )}
                {selected && withExtraSlots && (
                  <td>
                    {!!value[choice.id] && choice.price !== 0 && (
                      <span style={{whiteSpace: 'nowrap'}}>
                        <b>Total</b>: {formatPrice(choice)} {currency}
                      </span>
                    )}
                  </td>
                )}
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
