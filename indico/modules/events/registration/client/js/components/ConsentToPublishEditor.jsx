// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import registrationChangeConsent from 'indico-url:event_registration.api_registration_change_consent';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Icon} from 'semantic-ui-react';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import ConsentToPublishDropdown, {publishModePropType} from './ConsentToPublishDropdown';

import './ConsentToPublishEditor.module.scss';

export default function ConsentToPublishEditor({
  locator,
  publishToParticipants,
  publishToPublic,
  initialConsentToPublish,
}) {
  const [consentToPublish, setConsentToPublish] = useState(initialConsentToPublish);
  const [status, setStatus] = useState('');

  async function editConsentToPublish(value) {
    setConsentToPublish(value);
    setStatus('loading');
    try {
      await indicoAxios.post(registrationChangeConsent(locator), {consent_to_publish: value});
      setStatus('success');
    } catch (error) {
      setStatus('error');
      setConsentToPublish(consentToPublish);
      return handleAxiosError(error);
    }
  }

  return (
    <div styleName="consent-dropdown-container">
      <ConsentToPublishDropdown
        publishToParticipants={publishToParticipants}
        publishToPublic={publishToPublic}
        onChange={evt => editConsentToPublish(evt.target.value)}
        value={consentToPublish}
        loading={status === 'loading'}
        disabled={status === 'loading'}
      />
      {status === 'success' && <Icon name="check" color="green" />}
      {status === 'error' && <Icon name="x" color="red" />}
    </div>
  );
}

ConsentToPublishEditor.propTypes = {
  locator: PropTypes.object.isRequired,
  publishToParticipants: publishModePropType.isRequired,
  publishToPublic: publishModePropType.isRequired,
  initialConsentToPublish: PropTypes.oneOf(['nobody', 'participants', 'all']).isRequired,
};
