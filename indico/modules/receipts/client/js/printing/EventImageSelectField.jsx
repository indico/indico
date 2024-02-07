// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Form, Header, HeaderContent, HeaderSubheader, Image} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

const imageShape = {
  identifier: PropTypes.string.isRequired,
  filename: PropTypes.string.isRequired,
  url: PropTypes.string.isRequired,
};

const imageSource = {
  images: Translate.string('from Images'),
  attachments: Translate.string('from Materials'),
  logo: Translate.string('from Event'),
};

const EventImageSelectField = ({name, label, value, required, onChange, onOpen, eventImages}) => (
  <Form.Dropdown
    label={label}
    name={name}
    options={eventImages.map(({identifier, filename, url}) => ({
      key: identifier,
      value: identifier,
      text: filename,
      content: (
        <Header style={{fontSize: 14}}>
          <Image src={url} />
          <HeaderContent>
            {filename}
            <HeaderSubheader content={imageSource[identifier.split('/', 1)[0]]} />
          </HeaderContent>
        </Header>
      ),
    }))}
    noResultsMessage={Translate.string('No images were found in this event.')}
    value={value}
    required={required}
    selectOnNavigation={false}
    selectOnBlur={false}
    clearable={!required}
    onChange={(_, {value: v}) => onChange(v)}
    onOpen={onOpen}
    selection
    search
  />
);

EventImageSelectField.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  value: PropTypes.string,
  required: PropTypes.bool,
  onChange: PropTypes.func,
  onOpen: PropTypes.func,
  eventImages: PropTypes.arrayOf(PropTypes.shape(imageShape)),
};

EventImageSelectField.defaultProps = {
  value: null,
  required: false,
  onChange: () => {},
  onOpen: () => {},
  eventImages: [],
};

export default EventImageSelectField;
