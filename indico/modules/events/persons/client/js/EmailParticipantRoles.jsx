// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import emailMetadataURL from 'indico-url:persons.api_email_event_persons_metadata';
import emailSendURL from 'indico-url:persons.api_email_event_persons_send';
import emailPreviewURL from 'indico-url:persons.email_event_persons_preview';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Dimmer, Loader} from 'semantic-ui-react';

import {handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {indicoAxios} from 'indico/utils/axios';

import {EmailDialog} from './EmailDialog';

export function EmailParticipantRoles({
  eventId,
  roleIds,
  persons,
  onClose,
  onSubmitSucceeded,
  noAccount,
  notInvitedOnly,
  successTimeout,
}) {
  const [sentCount, setSentCount] = useState(0);
  const recipientData = {
    role_id: roleIds,
    persons,
    no_account: noAccount,
    not_invited_only: notInvitedOnly,
  };
  const {data, loading} = useIndicoAxios({
    url: emailMetadataURL({event_id: eventId}),
    method: 'POST',
    data: recipientData,
  });
  const {
    senders = [],
    recipients = [],
    subject: defaultSubject,
    body: defaultBody,
    placeholders = [],
  } = data || {};

  const handleSubmit = async data => {
    const requestData = {...data, ...recipientData};
    let resp;
    try {
      resp = await indicoAxios.post(emailSendURL({event_id: eventId}), requestData);
    } catch (err) {
      return handleSubmitError(err);
    }
    setSentCount(resp.data.count);
    if (onSubmitSucceeded) {
      onSubmitSucceeded(resp.data.count);
    }
    setTimeout(() => onClose(), successTimeout);
  };

  if (loading) {
    return (
      <Dimmer active page inverted>
        <Loader />
      </Dimmer>
    );
  }

  return (
    <EmailDialog
      onSubmit={handleSubmit}
      onClose={onClose}
      senders={senders}
      recipients={recipients}
      previewURL={emailPreviewURL({event_id: eventId})}
      previewContext={recipientData}
      placeholders={placeholders}
      initialFormValues={{subject: defaultSubject, body: defaultBody}}
      sentEmailsCount={sentCount}
    />
  );
}

EmailParticipantRoles.propTypes = {
  eventId: PropTypes.number.isRequired,
  roleIds: PropTypes.arrayOf(PropTypes.number),
  persons: PropTypes.arrayOf(PropTypes.string),
  onClose: PropTypes.func.isRequired,
  onSubmitSucceeded: PropTypes.func,
  noAccount: PropTypes.bool,
  notInvitedOnly: PropTypes.bool,
  successTimeout: PropTypes.number,
};

EmailParticipantRoles.defaultProps = {
  roleIds: [],
  persons: [],
  onSubmitSucceeded: undefined,
  noAccount: false,
  notInvitedOnly: false,
  successTimeout: 5000,
};
