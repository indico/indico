// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Field} from 'react-final-form';
import {Form} from 'semantic-ui-react';

import {FinalInput, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {mapPropsToAttributes} from './util';

const attributeMap = {minValue: 'min', maxValue: 'max'};

export default function InputNumber({htmlName, disabled, ...props}) {
  const inputProps = mapPropsToAttributes(props, attributeMap, InputNumber.defaultProps);
  return <input type="number" name={htmlName} {...inputProps} disabled={disabled} />;
}

InputNumber.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  minValue: PropTypes.number,
  maxValue: PropTypes.number,
};

InputNumber.defaultProps = {
  disabled: false,
  minValue: 0,
  maxValue: null,
};

export function NumberSettings() {
  return (
    <Form.Group widths="equal">
      <Field name="maxValue" subscription={{value: true}}>
        {({input: {value: maxValue}}) => (
          <FinalInput
            name="minValue"
            type="number"
            label={Translate.string('Minimum')}
            placeholder={String(InputNumber.defaultProps.minValue)}
            step="1"
            min="0"
            validate={v.optional(v.range(0, maxValue || parseFloat('Infinity')))}
            fluid
          />
        )}
      </Field>
      <Field name="minValue" subscription={{value: true}}>
        {({input: {value: minValue}}) => (
          <FinalInput
            name="maxValue"
            type="number"
            label={Translate.string('Maximum')}
            placeholder={Translate.string('No maximum')}
            step="1"
            min="0"
            validate={v.optional(v.min(minValue || 0))}
            fluid
          />
        )}
      </Field>
    </Form.Group>
  );
}
