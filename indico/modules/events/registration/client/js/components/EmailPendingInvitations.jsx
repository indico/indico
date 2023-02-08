// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Dimmer, Loader} from 'semantic-ui-react';

import {EmailDialog} from 'indico/modules/events/persons/EmailDialog';
import {handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {indicoAxios} from 'indico/utils/axios';

export default function EmailPendingInvitations({metadataURL, previewURL, sendURL, onClose}) {
  const successTimeout = 5000;
  const [sentCount, setSentCount] = useState(0);

  const {data, loading} = useIndicoAxios(metadataURL);
  const {
    senders = [],
    recipients = [],
    subject: defaultSubject,
    body: defaultBody,
    placeholders = [],
  } = data || {};

  const handleSubmit = async data => {
    data.body = data.body.getData ? data.body.getData() : data.body;
    let resp;
    try {
      resp = await indicoAxios.post(sendURL, data);
    } catch (err) {
      return handleSubmitError(err);
    }
    setSentCount(resp.data.count);
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
      previewURL={previewURL}
      placeholders={placeholders}
      initialFormValues={{subject: defaultSubject, body: defaultBody}}
      sentEmailsCount={sentCount}
    />
  );
}

EmailPendingInvitations.propTypes = {
  metadataURL: PropTypes.string.isRequired,
  previewURL: PropTypes.string.isRequired,
  sendURL: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};
