// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Accordion, Form} from 'semantic-ui-react';

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

export default function TemplateParameterEditor({customFields, value, onChange, title}) {
  if (customFields.length === 0 || Object.keys(value).length === 0) {
    return null;
  }
  return (
    <Accordion
      defaultActiveIndex={0}
      panels={[
        {
          key: 'template-params',
          title,
          content: {
            content: customFields.map(({name, type, options}) => (
              <CustomField
                key={name}
                type={type}
                value={value[name]}
                onChange={v => {
                  onChange({...value, [name]: v});
                }}
                name={name}
                options={options}
              />
            )),
          },
        },
      ]}
      styled
      fluid
    />
  );
}

TemplateParameterEditor.propTypes = {
  customFields: PropTypes.array.isRequired,
  value: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
  title: PropTypes.string,
};

TemplateParameterEditor.defaultProps = {
  title: '',
};
