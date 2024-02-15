// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Accordion, Form} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';

import EventImageSelectField from './EventImageSelectField';

export const getDefaultFieldValue = f => {
  if (f.type === 'dropdown') {
    return f.attributes.options[f.attributes.default];
  } else if (f.type === 'checkbox') {
    return f.attributes.value || false;
  } else if (f.type === 'image') {
    return null;
  } else {
    return f.attributes.value || '';
  }
};

/**
 * This component represents a custom field which can contain a "text" (str), "choice" or "yes/no" (boolean).
 */
function CustomField({
  name,
  value,
  type,
  attributes,
  validations,
  onChange,
  eventImages,
  fetchImages,
  loadingImages,
}) {
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
  } else if (type === 'image') {
    return (
      <EventImageSelectField
        label={attributes.label}
        name={name}
        value={value}
        required={validations.required}
        loading={loadingImages}
        onChange={onChange}
        eventImages={eventImages}
        onRefresh={fetchImages && (() => fetchImages())}
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
  eventImages: PropTypes.arrayOf(PropTypes.object),
  fetchImages: PropTypes.func,
  loadingImages: PropTypes.bool,
};

CustomField.defaultProps = {
  value: null,
  eventImages: [],
  fetchImages: null,
  loadingImages: false,
};

export default function TemplateParameterEditor({
  customFields,
  value,
  onChange,
  title,
  fetchImagesURL,
  defaultOpen,
}) {
  const {data, loading, reFetch} = useIndicoAxios(
    {url: fetchImagesURL || ''},
    {camelize: true, manual: !customFields.some(f => f.type === 'image') || !fetchImagesURL}
  );
  const eventImages = fetchImagesURL
    ? data?.images || []
    : [
        {
          identifier: 'event://placeholder',
          filename: 'placeholder.png',
          preview: `${Indico.Urls.ImagesBase}/placeholder_image.svg`,
        },
      ];

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
                eventImages={eventImages}
                fetchImages={fetchImagesURL && reFetch}
                loadingImages={loading}
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
  fetchImagesURL: PropTypes.string,
  defaultOpen: PropTypes.bool,
};

TemplateParameterEditor.defaultProps = {
  title: '',
  fetchImagesURL: null,
  defaultOpen: false,
};
