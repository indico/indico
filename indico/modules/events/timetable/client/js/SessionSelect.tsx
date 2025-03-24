// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {Label} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import {FinalDropdown} from '../../../../../web/client/js/react/forms';

import {Session} from './types';

interface SessionOption {
  key: string;
  text: string | React.ReactNode;
  value: number;
}

interface SessionSelectProps {
  sessions?: Session[];
  [key: string]: unknown;
}

const processSessions = (sessions: Session[]) => {
  return sessions.length
    ? sessions.flatMap((session: Session): SessionOption[] => {
        const {backgroundColor: background, textColor: text} = session;
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

export function SessionSelect({sessions, ...rest}: SessionSelectProps) {
  const sessionOptions = processSessions(sessions || []);

  return (
    <FinalDropdown
      name="session_id"
      label={Translate.string('Session')}
      placeholder={Translate.string('Select a session')}
      options={sessionOptions}
      selection
      search={false}
      multiple={false}
      disabled={!sessions.length}
      {...rest}
    />
  );
}
