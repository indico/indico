// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form} from 'semantic-ui-react';

import {Markdown, toClasses} from 'indico/react/util';

import {fieldRegistry} from './fields/registry';

import '../../styles/regform.module.scss';

export default function FormItem({
  title,
  description,
  inputType,
  isEnabled,
  isRequired,
  sortHandle,
  setupMode,
  setupActions,
  ...rest
}) {
  const meta = fieldRegistry[inputType] || {};
  const InputComponent = meta.inputComponent;
  const {customFormItem} = meta;
  const inputProps = {title, description, isRequired, isEnabled, ...rest};
  return (
    <div styleName={`form-item ${toClasses({disabled: !isEnabled, editable: setupMode})}`}>
      {sortHandle}
      <div styleName="content">
        {InputComponent ? (
          customFormItem ? (
            <InputComponent
              isRequired={isRequired || meta.alwaysRequired}
              disabled={!isEnabled}
              {...inputProps}
            />
          ) : (
            <Form.Field
              required={isRequired || meta.alwaysRequired}
              disabled={!isEnabled}
              styleName="field"
            >
              <label>{title}</label>
              <InputComponent isRequired={isRequired || meta.alwaysRequired} {...inputProps} />
            </Form.Field>
          )
        ) : (
          `Unknown input type: ${inputType}`
        )}
        {description && (
          <div styleName="description">
            <Markdown>{description}</Markdown>
          </div>
        )}
      </div>
      {setupActions && <div styleName="actions">{setupActions}</div>}
    </div>
  );
}

FormItem.propTypes = {
  id: PropTypes.number.isRequired,
  title: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  isEnabled: PropTypes.bool.isRequired,
  position: PropTypes.number.isRequired,
  /** Whether the field is required during registration */
  isRequired: PropTypes.bool,
  /** Whether the field is a special "personal data" field */
  fieldIsPersonalData: PropTypes.bool,
  /** Whether the field cannot be disabled */
  fieldIsRequired: PropTypes.bool,
  /** The HTML input name of the field (empty in case of static text) */
  htmlName: PropTypes.string,
  /** The widget type of the field */
  inputType: PropTypes.string.isRequired,
  /** The handle to sort the section during setup */
  sortHandle: PropTypes.node,
  /** Whether the field is being shown during form setup */
  setupMode: PropTypes.bool,
  /** Actions available during form setup */
  setupActions: PropTypes.node,
  // ... and various other field-specific keys (billing, limited-places, other config)
};

FormItem.defaultProps = {
  fieldIsPersonalData: false,
  fieldIsRequired: false,
  isRequired: false,
  htmlName: null,
  sortHandle: null,
  setupMode: false,
  setupActions: null,
};
