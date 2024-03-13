// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import emailMetadataURL from 'indico-url:surveys.manage_email_event_survey_metadata';
import emailPreviewURL from 'indico-url:surveys.manage_email_event_survey_preview';
import emailSendURL from 'indico-url:surveys.manage_email_event_survey_send';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Dimmer, Loader} from 'semantic-ui-react';

import {FinalEmailList} from 'indico/react/components';
import {FinalCheckbox, handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {EmailDialog} from '../../../persons/client/js/EmailDialog';

export function EmailSurveyParticipants({eventId, surveyId, onClose}) {
  const [sentCount, setSentCount] = useState(0);
  const {data, loading} = useIndicoAxios({
    url: emailMetadataURL({event_id: eventId, survey_id: surveyId}),
    method: 'POST',
  });
  const {senders = [], subject: defaultSubject, body: defaultBody, placeholders = []} = data || {};

  const handleSubmit = async data => {
    const requestData = {...data};
    let resp;
    try {
      resp = await indicoAxios.post(
        emailSendURL({event_id: eventId, survey_id: surveyId}),
        requestData
      );
    } catch (err) {
      return handleSubmitError(err);
    }
    setSentCount(resp.data.count);
    setTimeout(() => onClose(), 5000);
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
      recipientsField={
        <>
          <FinalCheckbox
            name="email_all_participants"
            label={Translate.string('Send email to all event participants')}
            toggle
          />
          <FinalEmailList
            name="recipients_addresses"
            label={Translate.string('Recipients addresses')}
            description={Translate.string('Send email to every address in this list')}
          />
        </>
      }
      previewURL={emailPreviewURL({event_id: eventId, survey_id: surveyId})}
      placeholders={placeholders}
      initialFormValues={{
        subject: defaultSubject,
        body: defaultBody,
        recipients_addresses: [],
        email_all_participants: false,
      }}
      sentEmailsCount={sentCount}
    />
  );
}

EmailSurveyParticipants.propTypes = {
  eventId: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
  surveyId: PropTypes.number.isRequired,
};
