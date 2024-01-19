// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import PropTypes from 'prop-types';
import React, {useState} from 'react';

import {Translate} from 'indico/react/i18n';

import {EmailSurveyParticipants} from './EmailSurveyParticipants';

export function EmailSurveyParticipantsButton({eventId, surveyId}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        className="i-button icon-mail"
        onClick={evt => {
          if (!evt.target.classList.contains('disabled')) {
            setOpen(true);
          }
        }}
      >
        <Translate>Email</Translate>
      </button>
      {open && (
        <EmailSurveyParticipants
          eventId={eventId}
          surveyId={surveyId}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

EmailSurveyParticipantsButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  surveyId: PropTypes.number.isRequired,
};
