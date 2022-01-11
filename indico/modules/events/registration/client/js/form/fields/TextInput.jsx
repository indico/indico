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

const attributeMap = {length: 'size', minLength: 'minLength', maxLength: 'maxLength'};

export default function TextInput({htmlName, disabled, title, isRequired, ...props}) {
  const inputProps = mapPropsToAttributes(props, attributeMap, TextInput.defaultProps);
  return (
    <Form.Field required={isRequired} disabled={disabled} styleName="field">
      <label>{title}</label>
      <input type="text" name={htmlName} {...inputProps} />
    </Form.Field>
  );
}

TextInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
  length: PropTypes.number,
  minLength: PropTypes.number,
  maxLength: PropTypes.number,
};

TextInput.defaultProps = {
  disabled: false,
  length: 60,
  minLength: null,
  maxLength: null,
};

export function TextSettings() {
  return (
    <Form.Group widths="equal">
      <FinalInput
        name="length"
        type="number"
        label={Translate.string('Width')}
        placeholder={String(TextInput.defaultProps.length)}
        step="1"
        min="5"
        max="60"
        validate={v.optional(v.range(5, 60))}
        fluid
      />
      <FinalInput
        name="minLength"
        type="number"
        label={Translate.string('Min. length')}
        step="1"
        min="1"
        validate={v.optional(v.min(1))}
        fluid
      />
      <FinalInput
        name="maxLength"
        type="number"
        label={Translate.string('Max. length')}
        step="1"
        min="1"
        validate={v.optional(v.min(1))}
        fluid
      />
    </Form.Group>
  );
}
