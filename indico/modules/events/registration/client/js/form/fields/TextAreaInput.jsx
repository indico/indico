// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form} from 'semantic-ui-react';

import {FinalInput, FinalTextArea, validators as v} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import '../../../styles/regform.module.scss';

import {mapPropsToAttributes} from './util';

const attributeMap = {
  numberOfRows: 'rows',
};

export default function TextAreaInput({htmlId, htmlName, disabled, title, isRequired, ...props}) {
  const inputProps = mapPropsToAttributes(props, attributeMap, TextAreaInput.defaultProps);
  return (
    <FinalTextArea
      id={htmlId}
      name={htmlName}
      {...inputProps}
      disabled={disabled}
      required={isRequired}
      style={{resize: 'none'}}
    />
  );
}

TextAreaInput.propTypes = {
  htmlId: PropTypes.string.isRequired,
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  numberOfRows: PropTypes.number,
  title: PropTypes.string.isRequired,
  isRequired: PropTypes.bool.isRequired,
};

TextAreaInput.defaultProps = {
  disabled: false,
  numberOfRows: 2,
};

export function TextAreaSettings() {
  return (
    <Form.Group widths="equal">
      <FinalInput
        name="numberOfRows"
        type="number"
        label={Translate.string('Rows')}
        placeholder={String(TextAreaInput.defaultProps.numberOfRows)}
        step="1"
        min="1"
        max="20"
        validate={v.optional(v.range(1, 20))}
        fluid
      />
    </Form.Group>
  );
}
