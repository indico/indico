// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form} from 'semantic-ui-react';

/**
 * This component represents a custom field which can contain a "text" (str), "choice" or "yes/no" (boolean).
 */
function CustomField({name, value, type, options, onChange}) {
  if (type === 'str') {
    return (
      <Form.Input
        label={name}
        name={name}
        value={value}
        onChange={(_, {value: v}) => onChange(v)}
      />
    );
  } else if (type === 'choice') {
    return (
      <Form.Dropdown
        label={name}
        name={name}
        options={options.map(option => ({value: option, key: option, text: option}))}
        value={value}
        selection
        onChange={(_, {value: v}) => onChange(v)}
      />
    );
  } else {
    return (
      <Form.Checkbox
        label={name}
        name={name}
        onChange={(_, {checked}) => onChange(checked)}
        checked={value}
      />
    );
  }
}

CustomField.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]).isRequired,
  type: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(PropTypes.string),
  onChange: PropTypes.func.isRequired,
};

CustomField.defaultProps = {
  options: null,
};

export default function TemplateParameterEditor({customFields, values, onChange}) {
  return customFields.map(({name, type, options}) => (
    <CustomField
      key={name}
      type={type}
      value={values[name]}
      onChange={value => {
        onChange({...values, [name]: value});
      }}
      name={name}
      options={options}
    />
  ));
}

TemplateParameterEditor.propTypes = {
  customFields: PropTypes.array,
  values: PropTypes.object,
  onChange: PropTypes.func,
};

TemplateParameterEditor.defaultProps = {
  customFields: [],
};
