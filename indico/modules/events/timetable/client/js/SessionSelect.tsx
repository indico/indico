// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {DropdownItemProps, Icon} from 'semantic-ui-react';

import {FinalDropdown} from 'indico/react/forms/fields';
import {Translate} from 'indico/react/i18n';

import {Colors, Session} from './types';

import './SessionSelect.module.scss';

interface SessionOption {
  key: string;
  text: string | React.ReactNode;
  title: string;
  value: number;
}

interface SessionSelectProps {
  sessions: Session[];
  onCreateSession?: (session: Partial<Session>) => Session | Promise<Session>;
  [key: string]: unknown;
}

interface DropdownElementProps {
  title: string;
  colors?: Colors;
  children?: React.ReactNode;
}

function DropdownElement({title, colors, children}: DropdownElementProps) {
  const {color: subColor, backgroundColor: color} = colors || {};

  return (
    <span styleName="dropdown-element">
      {colors && (
        <Icon.Group>
          <Icon name="circle" style={{color}} />
          <Icon name="circle" styleName="sub-icon" size="mini" style={{color: subColor}} />
        </Icon.Group>
      )}
      {children}
      {title}
    </span>
  );
}

const _mapSessionsToOptions = (sessions: Session[]) => {
  return sessions.length
    ? sessions
        .flatMap((session: Session): SessionOption[] => {
          return [
            {
              key: `session:${session.id}`,
              text: <DropdownElement title={session.title} colors={session.colors} />,
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

export function SessionSelect({
  sessions: initialSessions,
  onCreateSession,
  ...rest
}: SessionSelectProps) {
  const [query, setQuery] = useState('');
  const [sessions, setSessions] = useState(initialSessions);
  let options = _mapSessionsToOptions(sessions || []);
  const [initialValue, setInitialValue] = useState(options[0]?.value);
  // Only disabled if you can't create a session with call back function
  const disabled = !(onCreateSession || sessions.length);
  const actions: DropdownItemProps[] = [];

  const _createSession = async () => {
    const session: Session = await onCreateSession({
      title: query,
      defaultContribDurationMinutes: 20,
    });
    setSessions([...sessions, session]);
    options = _mapSessionsToOptions([...sessions, session]);
    const selectedValue = options.find(opt => opt.value === session.id)?.value;

    if (selectedValue) {
      setInitialValue(selectedValue);
    }
  };

  if (onCreateSession) {
    actions.push({
      key: 'create',
      text: (
        <DropdownElement title={Translate.string("Create '{query}'", {query})}>
          <Icon name="plus" styleName="action-icon" />
        </DropdownElement>
      ),
      onClick: async () => await _createSession(),
    });
  }

  return (
    <FinalDropdown
      name="session_id"
      label={Translate.string('Session')}
      placeholder={
        sessions.length
          ? Translate.string('Select a session')
          : Translate.string('No sessions available')
      }
      options={[...options, ...actions]}
      selection
      disabled={disabled}
      multiple={false}
      initialValue={initialValue}
      // Using options instead of the argument (_) bypasses actions
      search={(_, q) => [..._filterOptions(options, q), ...actions]}
      onSearchChange={(_, {searchQuery: q}) => setQuery(q)}
      onKeyDown={e => {
        if (
          e.key === 'Enter' &&
          query &&
          onCreateSession &&
          !_filterOptions(options, query).length
        ) {
          e.preventDefault();
          _createSession();
        }
      }}
      {...rest}
    />
  );
}
