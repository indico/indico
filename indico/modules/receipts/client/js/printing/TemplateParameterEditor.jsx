// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Accordion, Form} from 'semantic-ui-react';

export const getDefaultFieldValue = f => {
  if (f.type === 'dropdown') {
    return f.attributes.options[f.attributes.default];
  } else if (f.type === 'checkbox') {
    return f.attributes.value || false;
  } else {
    return f.attributes.value || '';
  }
};

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

export default function TemplateParameterEditor({
  customFields,
  value,
  onChange,
  title,
  defaultOpen,
}) {
  if (customFields.length === 0 || Object.keys(value).length === 0) {
    return null;
  }
  return (
    <Accordion
      defaultActiveIndex={defaultOpen ? 0 : undefined}
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
  defaultOpen: PropTypes.bool,
};

TemplateParameterEditor.defaultProps = {
  title: '',
  defaultOpen: false,
};
