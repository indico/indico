// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
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

import {FinalDropdown, handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {EmailDialog} from './EmailDialog';

export function EmailSurveyParticipants({context, eventId, onClose}) {
  const [sentCount, setSentCount] = useState(0);
  const {data, loading} = useIndicoAxios({
    url: emailMetadataURL({event_id: eventId}),
    method: 'POST',
    data: context,
  });
  const {senders = [], subject: defaultSubject, body: defaultBody, placeholders = []} = data || {};

  const handleSubmit = async data => {
    const requestData = {...data, ...context};
    let resp;
    try {
      resp = await indicoAxios.post(emailSendURL({event_id: eventId}), requestData);
    } catch (err) {
      return handleSubmitError(err);
    }
    setSentCount(resp.data.count);
    setTimeout(() => onClose(), 5000);
  };

  const recipientRoles = [
    {name: 'speaker', title: Translate.string('Speaker')},
    {name: 'author', title: Translate.string('Author')},
    {name: 'coauthor', title: Translate.string('Co-author')},
    {name: 'submitter', title: Translate.string('Submitter')},
  ];

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
      previewURL={emailPreviewURL({event_id: eventId})}
      previewContext={context}
      placeholders={placeholders}
      initialFormValues={{subject: defaultSubject, body: defaultBody, recipient_roles: []}}
      sentEmailsCount={sentCount}
      recipientsField={
        <FinalDropdown
          name="recipient_roles"
          label={Translate.string('Send emails to these roles')}
          multiple
          selection
          options={recipientRoles.map(({name, title}) => ({value: name, text: title, key: name}))}
          required
        />
      }
    />
  );
}

EmailSurveyParticipants.propTypes = {
  context: PropTypes.object.isRequired,
  eventId: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
};
