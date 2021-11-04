// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {toClasses} from 'indico/react/util';

import InputLabel from './fields/InputLabel';
import InputText from './fields/InputText';

import '../../styles/regform.module.scss';

const fieldRegistry = {
  label: {noLabel: true, component: InputLabel},
  text: {component: InputText},
  // TODO add other input types
};

export default function FormItem({
  title,
  description,
  inputType,
  isEnabled,
  isRequired,
  sortHandle,
  ...rest
}) {
  const meta = fieldRegistry[inputType] || {noLabel: false, component: null};
  const InputComponent = meta.component;
  const inputProps = {title, description, isRequired, isEnabled, ...rest};
  return (
    <div styleName={`form-item editable ${toClasses({disabled: !isEnabled})}`}>
      {sortHandle}
      {!meta.noLabel && (
        <span styleName="label">
          {title}
          {isRequired && <span styleName="required">*</span>}
        </span>
      )}
      <div styleName="content">
        {InputComponent ? <InputComponent {...inputProps} /> : `Unknown input type: ${inputType}`}
        {description && <div className="field-description">{description}</div>}
      </div>
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
  // ... and various other field-specific keys (billing, limited-places, other config)
};

FormItem.defaultProps = {
  fieldIsPersonalData: false,
  fieldIsRequired: false,
  isRequired: false,
  htmlName: null,
  sortHandle: null,
};
