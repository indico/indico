// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form} from 'semantic-ui-react';

import {FinalInput, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {mapPropsToAttributes} from './util';

import '../../../styles/regform.module.scss';

const attributeMap = {minLength: 'minLength', maxLength: 'maxLength'};

export default function TextInput({htmlName, disabled, title, isRequired, ...props}) {
  const inputProps = mapPropsToAttributes(props, attributeMap, TextInput.defaultProps);
  return (
    <FinalInput
      type="text"
      name={htmlName}
      {...inputProps}
      required={isRequired}
      disabled={disabled}
    />
  );
}

TextInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
  minLength: PropTypes.number,
  maxLength: PropTypes.number,
};

TextInput.defaultProps = {
  disabled: false,
  minLength: 0,
  maxLength: 0,
};

export function TextSettings() {
  return (
    <Form.Group widths="equal">
      <FinalInput
        name="minLength"
        type="number"
        label={Translate.string('Min. length')}
        placeholder={String(TextInput.defaultProps.minLength)}
        step="1"
        min="0"
        validate={v.optional(v.or(v.chain(v.min(0), v.max(0)), v.min(2)))}
        format={val => val || ''}
        parse={val => +val || 0}
        fluid
      />
      <FinalInput
        name="maxLength"
        type="number"
        label={Translate.string('Max. length')}
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

export function textSettingsFormValidator({minLength, maxLength}) {
  if (minLength && maxLength && minLength > maxLength) {
    const msg = Translate.string('The minimum length cannot be greater than the maximum length.');
    return {
      minLength: msg,
      maxLength: msg,
    };
  }
}
