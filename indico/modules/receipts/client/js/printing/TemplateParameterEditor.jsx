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
function CustomField({name, value, type, attributes, validations, onChange}) {
  if (type === 'input') {
    return (
      <Form.Input
        label={attributes.label}
        name={name}
        value={value}
        required={validations.required}
        onChange={(_, {value: v}) => onChange(v)}
      />
    );
  } else if (type === 'textarea') {
    return (
      <Form.TextArea
        label={attributes.label}
        name={name}
        value={value}
        required={validations.required}
        onChange={(_, {value: v}) => onChange(v)}
      />
    );
  } else if (type === 'dropdown') {
    return (
      <Form.Dropdown
        label={attributes.label}
        name={name}
        options={attributes.options.map(o => ({value: o, key: o, text: o}))}
        value={value}
        selection
        required={validations.required}
        selectOnNavigation={false}
        selectOnBlur={false}
        clearable={!validations.required}
        onChange={(_, {value: v}) => onChange(v)}
      />
    );
  } else if (type === 'checkbox') {
    return (
      <Form.Checkbox
        label={attributes.label}
        name={name}
        onChange={(_, {checked}) => onChange(checked)}
        checked={value}
        required={validations.required}
      />
    );
  }
}

CustomField.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.number]),
  type: PropTypes.string.isRequired,
  attributes: PropTypes.object.isRequired,
  validations: PropTypes.shape({
    required: PropTypes.bool,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};

CustomField.defaultProps = {
  value: null,
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
            content: customFields.map(({name, type, attributes, validations = {}}) => (
              <CustomField
                key={name}
                type={type}
                value={value[name]}
                onChange={v => {
                  onChange({...value, [name]: v});
                }}
                name={name}
                attributes={attributes}
                validations={validations}
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
