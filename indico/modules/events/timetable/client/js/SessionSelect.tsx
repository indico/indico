// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import {DropdownItemProps, Icon} from 'semantic-ui-react';

import {FinalDropdown} from 'indico/react/forms/fields';
import {Translate} from 'indico/react/i18n';

import {Session} from './types';

import './SessionSelect.module.scss';

interface SessionOption {
  key: string;
  text: string | React.ReactNode;
  title: string;
  value: number;
}

interface SessionSelectProps {
  sessions: Session[];
  onCreateSession?: () => void;
  [key: string]: unknown;
}

const _getSessionElement = (session: Session) => {
  const {
    colors: {color: subColor, backgroundColor: color},
  } = session;
  return (
    <span>
      <Icon.Group styleName="session-icons">
        <Icon name="circle" style={{color}} />
        <Icon name="circle" styleName="sub-icon" size="mini" style={{color: subColor}} />
      </Icon.Group>
      {session.title}
    </span>
  );
};

const _mapSessionsToOptions = (sessions: Session[]) => {
  return sessions.length
    ? sessions
        .flatMap((session: Session): SessionOption[] => {
          return [
            {
              key: `session:${session.id}`,
              text: _getSessionElement(session),
              title: session.title,
              value: session.id,
            },
          ];
        })
        .sort((a, b) => a.title.toString().localeCompare(b.title.toString()))
    : [];
};

const _filterOptions = (options: DropdownItemProps[], query: string) => {
  const loweredQuery = query.toLowerCase();
  return options.filter(option => option.title.toLowerCase().includes(loweredQuery));
};

export function SessionSelect({sessions, onCreateSession, ...rest}: SessionSelectProps) {
  const options = _mapSessionsToOptions(sessions || []);
  const initialValue = options[0]?.value;
  // Only disabled if you can't create a session with call back function
  const disabled = !(onCreateSession || sessions.length);

  return (
    <FinalDropdown
      name="session_id"
      label={Translate.string('Session')}
      placeholder={
        sessions.length
          ? Translate.string('Select a session')
          : Translate.string('No sessions available')
      }
      options={options}
      selection
      disabled={disabled}
      multiple={false}
      initialValue={initialValue}
      search={(opts, query) => _filterOptions(opts, query)}
      {...rest}
    />
  );
}
