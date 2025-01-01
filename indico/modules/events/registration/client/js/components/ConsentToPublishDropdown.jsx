// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';

import {Select} from 'indico/react/components';
import {FinalField} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import './ConsentToPublishDropdown.module.scss';

export const publishModePropType = PropTypes.oneOf(['hide_all', 'show_with_consent', 'show_all']);

export default function ConsentToPublishDropdown({
  publishToParticipants,
  publishToPublic,
  value,
  useFinalForms,
  ...extraProps
}) {
  if (publishToParticipants === 'hide_all' && publishToPublic === 'hide_all') {
    return (
      <Translate>Your participation will only be visible to organizers of this event.</Translate>
    );
  } else if (publishToParticipants === 'show_all' && publishToPublic === 'hide_all') {
    return (
      <Translate>
        Your participation will be displayed to other participants of this event.
      </Translate>
    );
  } else if (publishToParticipants === 'show_all' && publishToPublic === 'show_all') {
    return (
      <Translate>
        Your participation will be displayed to everyone who can see this event.
      </Translate>
    );
  } else {
    const options = [];
    if (publishToParticipants === 'show_with_consent' || value === 'nobody') {
      options.push({
        key: 'nobody',
        value: 'nobody',
        label: Translate.string('Do not display my participation to anyone'),
        disabled: publishToParticipants !== 'show_with_consent',
      });
    }
    options.push({
      key: 'participants',
      value: 'participants',
      label: Translate.string('Display my participation only to other participants of this event'),
    });
    if (publishToPublic === 'show_with_consent' || value === 'all') {
      options.push({
        key: 'all',
        value: 'all',
        label: Translate.string('Display my participation to everyone who can see this event'),
        disabled: publishToPublic !== 'show_with_consent',
      });
    }
    return useFinalForms ? (
      <FinalField
        styleName="select"
        component={Select}
        options={options}
        required
        value={value}
        {...extraProps}
        id="input-consent-to-publish"
      />
    ) : (
      <Select
        styleName="select"
        options={options}
        value={value}
        required
        {...extraProps}
        id="input-consent-to-publish"
      />
    );
  }
}

ConsentToPublishDropdown.propTypes = {
  publishToParticipants: publishModePropType.isRequired,
  publishToPublic: publishModePropType.isRequired,
  value: PropTypes.oneOf(['nobody', 'participants', 'all']),
  useFinalForms: PropTypes.bool,
};

ConsentToPublishDropdown.defaultProps = {
  value: null,
  useFinalForms: false,
};
