// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {Dropdown, Label} from 'semantic-ui-react';

import {getRandomColors} from 'indico/modules/events/timetable/colors';
import {SessionIcon} from 'indico/modules/events/timetable/SessionIcon';
import {FormFieldAdapter} from 'indico/react/forms';
import {FinalField} from 'indico/react/forms/fields';
import {Translate} from 'indico/react/i18n';

import {Colors, Session} from './types';

import './SessionSelect.module.scss';

const DEFAULT_DRAFT_ID = -1;

interface CompactSession extends Pick<Session, 'title' | 'colors'> {
  id: typeof DEFAULT_DRAFT_ID | number;
}

interface SessionOption {
  key: `session:${string}`;
  text: string | React.ReactNode;
  title: string;
  value: typeof DEFAULT_DRAFT_ID | number;
}

interface SessionSelectProps {
  sessions: CompactSession[];
  value?: CompactSession | null;
  onChange?: (session: CompactSession) => void;
  [key: string]: unknown;
}

interface DropdownElementProps {
  title: string;
  colors?: Colors;
  children?: React.ReactNode;
}

function DropdownElement({title, colors, children}: DropdownElementProps) {
  return (
    <span styleName="dropdown-element">
      {colors && <SessionIcon colors={colors} />}
      {children}
      <span styleName="dropdown-element-title">{title}</span>
    </span>
  );
}

const _mapSessionToOption = (session: CompactSession): SessionOption => ({
  key: `session:${session.id}`,
  text: (
    <DropdownElement title={session.title} colors={session.colors}>
      {session.id === DEFAULT_DRAFT_ID && (
        <Label styleName="new-label" content={Translate.string('New session')} size="mini" />
      )}
    </DropdownElement>
  ),
  title: session.title,
  value: session.id,
});

const _mapSessionsToOptions = (sessions: CompactSession[]): SessionOption[] => {
  return sessions.length
    ? sessions
        .flatMap(_mapSessionToOption)
        .sort((a, b) => a.title.toString().localeCompare(b.title.toString()))
    : [];
};

const _filterOptions = (options: SessionOption[], query: string) => {
  const loweredQuery = query.toLowerCase();
  return options.filter(option => option.title.toLowerCase().includes(loweredQuery));
};

export function SessionSelect({value, sessions, onChange}: SessionSelectProps) {
  sessions = [...sessions]; // Avoid mutating the original array when adding draft session
  const [query, setQuery] = useState('');
  const [options, setOptions] = useState<SessionOption[]>(_mapSessionsToOptions(sessions || []));

  const _onChangeValue = (id: number) => {
    const selectedSession = sessions.find(s => s.id === id);

    if (id !== DEFAULT_DRAFT_ID) {
      sessions = sessions.filter(s => s.id !== DEFAULT_DRAFT_ID);
      setOptions(options.filter(o => o.value !== DEFAULT_DRAFT_ID));
    }

    onChange(selectedSession);
  };

  const _sortOptionsFn = (a: SessionOption, b: SessionOption) =>
    a.title.toString().localeCompare(b.title.toString());

  const _createDraftSessionOption = () => {
    const draftSession: CompactSession = {
      id: DEFAULT_DRAFT_ID,
      title: query,
      colors: getRandomColors(),
    };
    const draftSessionOption = _mapSessionToOption(draftSession);

    sessions = [draftSession, ...sessions.filter(s => s.id !== draftSession.id)];
    const newOptions = options.filter(o => o.value !== DEFAULT_DRAFT_ID);

    setOptions([draftSessionOption, ...newOptions.toSorted(_sortOptionsFn)]);
    _onChangeValue(draftSession.id);
  };

  return (
    <Dropdown
      styleName="session-select"
      placeholder={
        sessions.length
          ? Translate.string('Select a session')
          : Translate.string('Create a session by typing its title')
      }
      options={options}
      selection
      multiple={false}
      value={value?.id}
      onChange={(_, {value: id}) => _onChangeValue(id as number)}
      allowAdditions
      additionLabel={`${Translate.string('Create', {context: 'Session'})} `}
      additionPosition="bottom"
      onAddItem={() => _createDraftSessionOption()}
      search={(_, q) => _filterOptions(options, q)}
      onSearchChange={(_, {searchQuery: q}) => setQuery(q)}
    />
  );
}

interface SessionSelectAdapterProps {
  input: {
    value: CompactSession | null;
    onChange: (session: Session) => void;
  };
}

const SessionSelectAdapter: React.FC<SessionSelectAdapterProps> = ({input, ...rest}) => {
  return <FormFieldAdapter input={input} {...rest} as={SessionSelect} />;
};

export function FinalSessionSelect({sessions, ...rest}: SessionSelectProps) {
  return (
    <FinalField
      name="session_object"
      required
      label={Translate.string('Session')}
      adapter={SessionSelectAdapter}
      sessions={sessions}
      {...rest}
    />
  );
}
