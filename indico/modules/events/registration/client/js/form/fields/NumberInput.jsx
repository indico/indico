// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {useSelector} from 'react-redux';
import {Form, Label} from 'semantic-ui-react';

import {FinalInput, FinalField, validators as v, parsers as p} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {getPriceFormatter} from '../../form/selectors';

import '../../../styles/regform.module.scss';

function NumberInputComponent({id, value, onChange, disabled, price, minValue, maxValue}) {
  const formatPrice = useSelector(getPriceFormatter);
  const total = (value * price).toFixed(2);

  return (
    <div styleName="number-field">
      <input
        id={id}
        type="number"
        value={value !== null ? value : ''}
        min={minValue}
        max={maxValue || undefined}
        disabled={disabled}
        onChange={evt => onChange(evt.target.value ? +evt.target.value : null)}
      />
      {!!price && (
        <Label pointing="left" styleName="price-tag">
          {formatPrice(price)} (Total: {formatPrice(total)})
        </Label>
      )}
    </div>
  );
}

NumberInputComponent.propTypes = {
  id: PropTypes.string.isRequired,
  value: PropTypes.number,
  onChange: PropTypes.func.isRequired,
  disabled: PropTypes.bool.isRequired,
  price: PropTypes.number.isRequired,
  minValue: PropTypes.number.isRequired,
  maxValue: PropTypes.number,
};

NumberInputComponent.defaultProps = {
  value: null,
  maxValue: null,
};

export default function NumberInput({
  htmlId,
  htmlName,
  disabled,
  isRequired,
  price,
  minValue,
  maxValue,
}) {
  const validate = isRequired
    ? v.chain(v.required, v.number(), v.range(minValue, maxValue || Infinity))
    : v.chain(v.optional(), v.number(), v.range(minValue, maxValue || Infinity));
  return (
    <FinalField
      id={htmlId}
      name={htmlName}
      component={NumberInputComponent}
      required={isRequired}
      disabled={disabled}
      allowNull
      price={price}
      minValue={minValue}
      maxValue={maxValue}
      parse={p.number}
      validate={validate}
    />
  );
}

NumberInput.propTypes = {
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  isRequired: PropTypes.bool,
  price: PropTypes.number,
  minValue: PropTypes.number,
  maxValue: PropTypes.number,
};

NumberInput.defaultProps = {
  disabled: false,
  isRequired: false,
  price: 0,
  minValue: 0,
  maxValue: 0,
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
        parse={val => +val || 0}
        fluid
      />
      <FinalInput
        name="maxValue"
        type="number"
        label={Translate.string('Maximum')}
        placeholder={Translate.string('No maximum')}
        step="1"
        min="0"
        validate={v.optional(v.min(0))}
        format={val => val || ''}
        parse={val => +val || 0}
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
