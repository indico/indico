// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {
  Form,
  Header,
  HeaderContent,
  HeaderSubheader,
  Icon,
  IconGroup,
  Popup,
} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './EventImageSelectField.module.scss';

const imageShape = {
  identifier: PropTypes.string.isRequired,
  filename: PropTypes.string.isRequired,
  preview: PropTypes.string.isRequired,
};

const imageSource = {
  images: Translate.string('from Images'),
  attachments: Translate.string('from Materials'),
  logo: Translate.string('Event Logo'),
};

function EventImageOption({identifier, filename, preview}) {
  return (
    <Header styleName="option-header">
      <div
        styleName="preview"
        style={preview ? {backgroundImage: `url('data:image/jpeg;base64,${preview}')`} : undefined}
      >
        {!preview && (
          <IconGroup size="big">
            <Icon name="file image" color="grey" />
            <Icon corner="bottom right" name="dont" color="grey" />
          </IconGroup>
        )}
      </div>
      <HeaderContent>
        {!preview && (
          <Popup
            content={Translate.string(
              'This field only accepts jpg, png, gif and webp picture formats.'
            )}
            trigger={<Icon name="warning sign" />}
          />
        )}
        {filename}
        <HeaderSubheader content={imageSource[new URL(identifier).host]} />
      </HeaderContent>
    </Header>
  );
}

EventImageOption.propTypes = imageShape;

export default function EventImageSelectField({
  name,
  label,
  value,
  required,
  loading,
  onChange,
  onOpen,
  eventImages,
}) {
  return (
    <Form.Dropdown
      label={label}
      name={name}
      options={eventImages.map(image => ({
        key: image.identifier,
        value: image.identifier,
        text: image.filename,
        disabled: !image.preview,
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
}

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
