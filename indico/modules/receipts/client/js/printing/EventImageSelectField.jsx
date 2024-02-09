// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form, Header, HeaderContent, HeaderSubheader, Icon, IconGroup} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './EventImageSelectField.module.scss';

const imageShape = {
  identifier: PropTypes.string.isRequired,
  filename: PropTypes.string.isRequired,
  preview: PropTypes.string.isRequired,
  supported: PropTypes.bool.isRequired,
};

const imageSource = {
  images: Translate.string('from Images'),
  attachments: Translate.string('from Materials'),
  logo: Translate.string('from Logo'),
};

const EventImageOption = ({identifier, filename, preview, supported}) => (
  <Header styleName="option-header">
    <div
      styleName="preview"
      style={preview ? {backgroundImage: `url('data:image/jpeg;base64,${preview}')`} : undefined}
    >
      {!preview && (
        <IconGroup size="big">
          <Icon name="file image" />
          <Icon corner="bottom right" name="dont" />
        </IconGroup>
      )}
    </div>
    <HeaderContent>
      {filename} {!supported && <Translate as="em">(unsupported image type)</Translate>}
      <HeaderSubheader content={imageSource[new URL(identifier).host]} />
    </HeaderContent>
  </Header>
);

EventImageOption.propTypes = imageShape;

const EventImageSelectField = ({
  name,
  label,
  value,
  required,
  loading,
  onChange,
  onOpen,
  eventImages,
}) => (
  <Form.Dropdown
    label={label}
    name={name}
    options={eventImages.map(image => ({
      key: image.identifier,
      value: image.identifier,
      text: image.filename,
      disabled: !image.supported,
      content: <EventImageOption {...image} />,
    }))}
    noResultsMessage={
      loading
        ? Translate.string('Loading images...')
        : Translate.string('No images were found in this event.')
    }
    value={value}
    required={required}
    loading={loading}
    selectOnNavigation={false}
    selectOnBlur={false}
    clearable={!required}
    onChange={(_, {value: v}) => onChange(v)}
    onOpen={onOpen}
    styleName="image-select-field"
    selection
    search
  />
);

EventImageSelectField.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  value: PropTypes.string,
  required: PropTypes.bool,
  loading: PropTypes.bool,
  onChange: PropTypes.func,
  onOpen: PropTypes.func,
  eventImages: PropTypes.arrayOf(PropTypes.shape(imageShape)),
};

EventImageSelectField.defaultProps = {
  value: null,
  required: false,
  loading: false,
  onChange: () => {},
  onOpen: () => {},
  eventImages: [],
};

export default EventImageSelectField;
