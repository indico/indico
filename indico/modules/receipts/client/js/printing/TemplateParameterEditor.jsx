// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Accordion, Checkbox, Dropdown, Form, Input, TextArea} from 'semantic-ui-react';

import {PlaceholderInfo} from 'indico/react/components';
import {useIndicoAxios} from 'indico/react/hooks';

import EventImageSelectField from './EventImageSelectField';

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
  const id = `receipt-custom-${name}`;
  const placeholderWidget = attributes.placeholders && (
    <PlaceholderInfo
      placeholders={Object.entries(attributes.placeholders).map(
        ([placeholderName, description]) => ({
          name: placeholderName,
          description,
        })
      )}
    />
  );
  if (type === 'input') {
    return (
      <Form.Field required={validations.required}>
        <label htmlFor={id}>{attributes.label}</label>
        <Input
          name={name}
          id={id}
          value={value}
          required={validations.required}
          onChange={(_, {value: v}) => onChange(v)}
        />
        {attributes.description && <p className="field-description">{attributes.description}</p>}
        {placeholderWidget}
      </Form.Field>
    );
  } else if (type === 'textarea') {
    return (
      <Form.Field required={validations.required}>
        <label htmlFor={id}>{attributes.label}</label>
        <TextArea
          name={name}
          id={id}
          value={value}
          required={validations.required}
          onChange={(_, {value: v}) => onChange(v)}
        />
        {attributes.description && <p className="field-description">{attributes.description}</p>}
        {placeholderWidget}
      </Form.Field>
    );
  } else if (type === 'dropdown') {
    return (
      <Form.Field required={validations.required}>
        <label htmlFor={id}>{attributes.label}</label>
        <Dropdown
          name={name}
          id={id}
          options={attributes.options.map(o => ({value: o, key: o, text: o}))}
          value={value}
          selection
          required={validations.required}
          selectOnNavigation={false}
          selectOnBlur={false}
          clearable={!validations.required}
          onChange={(_, {value: v}) => onChange(v)}
        />
        {attributes.description && <p className="field-description">{attributes.description}</p>}
      </Form.Field>
    );
  } else if (type === 'checkbox') {
    return (
      <Form.Field required={validations.required}>
        <Checkbox
          label={attributes.label}
          name={name}
          onChange={(_, {checked}) => onChange(checked)}
          checked={value}
          required={validations.required}
        />
        {attributes.description && <p className="field-description">{attributes.description}</p>}
      </Form.Field>
    );
  } else if (type === 'image') {
    return (
      <EventImageSelectField
        label={attributes.label}
        name={name}
        description={attributes.description}
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
  attributes: PropTypes.shape({
    label: PropTypes.string.isRequired,
    description: PropTypes.string,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
    options: PropTypes.arrayOf(PropTypes.string),
    default: PropTypes.number,
    placeholders: PropTypes.objectOf(PropTypes.string),
  }).isRequired,
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
            content: customFields.map(({name, description, type, attributes, validations = {}}) => (
              <CustomField
                key={name}
                type={type}
                value={value[name]}
                onChange={v => {
                  onChange({...value, [name]: v});
                }}
                name={name}
                description={description}
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
