// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React from 'react';
import {Dropdown} from 'semantic-ui-react';

import {FinalDropdown} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

export const publishModePropType = PropTypes.oneOf(['hide_all', 'show_with_consent', 'show_all']);

export default function ConsentToPublishDropdown({
  publishToParticipants,
  publishToPublic,
  value,
  maximumConsentToPublish,
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
        text: Translate.string('Do not display my participation to anyone'),
        disabled: publishToParticipants !== 'show_with_consent',
      });
    }
    if (maximumConsentToPublish !== 'nobody') {
      options.push({
        key: 'participants',
        value: 'participants',
        text: Translate.string('Display my participation only to other participants of this event'),
      });
    }
    if (
      maximumConsentToPublish === 'all' &&
      (publishToPublic === 'show_with_consent' || value === 'all')
    ) {
      options.push({
        key: 'all',
        value: 'all',
        text: Translate.string('Display my participation to everyone who can see this event'),
        disabled: publishToPublic !== 'show_with_consent',
      });
    }
    return useFinalForms ? (
      <FinalDropdown options={options} selection required fluid {...extraProps} />
    ) : (
      <Dropdown options={options} selection fluid value={value} {...extraProps} />
    );
  }
}

ConsentToPublishDropdown.propTypes = {
  publishToParticipants: publishModePropType.isRequired,
  publishToPublic: publishModePropType.isRequired,
  value: PropTypes.oneOf(['nobody', 'participants', 'all']),
  maximumConsentToPublish: PropTypes.oneOf(['nobody', 'participants', 'all']),
  useFinalForms: PropTypes.bool,
};

ConsentToPublishDropdown.defaultProps = {
  value: null,
  maximumConsentToPublish: 'all',
  useFinalForms: false,
};
