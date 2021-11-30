// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {useSelector} from 'react-redux';
import {Form, Label} from 'semantic-ui-react';

import {FinalInput, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../../form_setup/selectors';

import {mapPropsToAttributes} from './util';

import '../../../styles/regform.module.scss';

const attributeMap = {minValue: 'min', maxValue: 'max'};

export default function NumberInput({htmlName, disabled, price, title, isRequired, ...props}) {
  const [value, setValue] = useState('');
  const currency = useSelector(getCurrency);
  const inputProps = mapPropsToAttributes(props, attributeMap, NumberInput.defaultProps);
  const total = (value * price).toFixed(2);

  return (
    <Form.Field required={isRequired} disabled={disabled} styleName="field">
      <label>{title}</label>
      <div styleName="number-field">
        <input
          type="number"
          name={htmlName}
          value={value}
          {...inputProps}
          onChange={evt => setValue(evt.target.value ? +evt.target.value : '')}
        />
        <Label pointing="left" styleName="price-tag">
          {price.toFixed(2)} {currency} (Total: {total} {currency})
        </Label>
      </div>
    </Form.Field>
  );
}

NumberInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  minValue: PropTypes.number,
  maxValue: PropTypes.number,
  price: PropTypes.number,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
};

NumberInput.defaultProps = {
  disabled: false,
  minValue: 0,
  maxValue: null,
  price: 0,
};

export function NumberSettings() {
  return (
    <Form.Group widths="equal">
      <FinalInput
        name="minValue"
        type="number"
        label={Translate.string('Minimum')}
        placeholder={String(NumberInput.defaultProps.minValue)}
        step="1"
        min="0"
        validate={v.optional(v.min(0))}
        format={val => val || ''}
        fluid
      />
      <FinalInput
        name="maxValue"
        type="number"
        label={Translate.string('Maximum')}
        placeholder={Translate.string('No maximum')}
        step="1"
        min="1"
        validate={v.optional(v.min(1))}
        fluid
      />
    </Form.Group>
  );
}

export function numberSettingsFormValidator({minValue, maxValue}) {
  if (minValue && maxValue && minValue > maxValue) {
    const msg = Translate.string('The minimum value cannot be greater than the maximum value.');
    return {
      minValue: msg,
      maxValue: msg,
    };
  }
}
