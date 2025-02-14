// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import sessionListURL from 'indico-url:sessions.api_session_list';

import React from 'react';
import {Label} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import {FinalDropdown} from '../forms';

interface Session {
  id: number;
  title: string;
  colors: {
    background: string;
    text: string;
  };
}

interface SessionSelectProps {
  eventId: number;
  onChange?: (value: any) => void;
  required?: boolean;
}

const processSessions = (sessions: Session[]) => {
  return sessions.length
    ? sessions.flatMap(session => {
        const {background, text} = session.colors;
        return [
          {
            key: `session:${session.id}`,
            text: <Label style={{background, color: text}}>{session.title}</Label>,
            value: session.id,
          },
        ];
      })
    : [];
};

export function SessionSelect({eventId, required}: SessionSelectProps) {
  const {data} = useIndicoAxios(sessionListURL({event_id: eventId}), {camelize: true});
  const sessions = processSessions(data || []);

  return (
    <FinalDropdown
      name="session_id"
      label={Translate.string('Session')}
      placeholder={Translate.string('Select a session')}
      options={sessions}
      required={required}
      selection
      multiple={undefined}
    />
  );
}
