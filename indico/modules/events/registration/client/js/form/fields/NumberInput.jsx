// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';
import {Form, Label} from 'semantic-ui-react';

import {FinalInput, FinalField, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getCurrency} from '../../form_setup/selectors';

import '../../../styles/regform.module.scss';

function NumberInputComponent({value, onChange, disabled, price, minValue, maxValue}) {
  const currency = useSelector(getCurrency);
  const total = (value * price).toFixed(2);

  return (
    <div styleName="number-field">
      <input
        type="number"
        value={value}
        min={minValue}
        max={maxValue}
        disabled={disabled}
        onChange={evt => onChange(evt.target.value ? +evt.target.value : '')}
      />
      <Label pointing="left" styleName="price-tag">
        {price.toFixed(2)} {currency} (Total: {total} {currency})
      </Label>
    </div>
  );
}

NumberInputComponent.propTypes = {
  value: PropTypes.oneOfType([PropTypes.number, PropTypes.oneOf([''])]).isRequired,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  price: PropTypes.number.isRequired,
  minValue: PropTypes.number.isRequired,
  maxValue: PropTypes.number,
};

NumberInputComponent.defaultProps = {
  maxValue: null,
};

export default function NumberInput({
  htmlName,
  disabled,
  isRequired,
  defaultValue,
  price,
  minValue,
  maxValue,
}) {
  return (
    <FinalField
      name={htmlName}
      component={NumberInputComponent}
      required={isRequired}
      disabled={disabled}
      defaultValue={defaultValue}
      price={price}
      minValue={minValue}
      maxValue={maxValue}
      parse={x => x} // Prevent empty string being coerced to undefined
      validate={v.or(value => {
        if (value !== '' || (isRequired && value === '')) {
          return Translate.string('This field is required.');
        }
      }, v.range(minValue, maxValue || Infinity))}
    />
  );
}

NumberInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  defaultValue: PropTypes.oneOfType([PropTypes.number, PropTypes.oneOf([''])]),
  price: PropTypes.number,
  minValue: PropTypes.number,
  maxValue: PropTypes.number,
};

NumberInput.defaultProps = {
  disabled: false,
  isRequired: false,
  defaultValue: '',
  price: 0,
  minValue: 0,
  maxValue: null,
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
