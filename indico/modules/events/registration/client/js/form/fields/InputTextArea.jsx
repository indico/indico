// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
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

const attributeMap = {
  numberOfRows: 'rows',
  numberOfColumns: 'cols',
};

export default function InputTextArea({htmlName, disabled, ...props}) {
  const inputProps = mapPropsToAttributes(props, attributeMap, InputTextArea.defaultProps);
  return <textarea name={htmlName} {...inputProps} disabled={disabled} style={{resize: 'none'}} />;
}

InputTextArea.propTypes = {
  htmlName: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  numberOfRows: PropTypes.number,
  numberOfColumns: PropTypes.number,
};

InputTextArea.defaultProps = {
  disabled: false,
  numberOfRows: 2,
  numberOfColumns: 60,
};

export function TextAreaSettings() {
  return (
    <Form.Group widths="equal">
      <FinalInput
        name="numberOfColumns"
        type="number"
        label={Translate.string('Columns')}
        placeholder={String(InputTextArea.defaultProps.numberOfColumns)}
        step="1"
        min="1"
        max="60"
        validate={v.optional(v.range(1, 60))}
        fluid
      />
      <FinalInput
        name="numberOfRows"
        type="number"
        label={Translate.string('Rows')}
        placeholder={String(InputTextArea.defaultProps.numberOfRows)}
        step="1"
        min="1"
        max="20"
        validate={v.optional(v.range(1, 20))}
        fluid
      />
    </Form.Group>
  );
}
