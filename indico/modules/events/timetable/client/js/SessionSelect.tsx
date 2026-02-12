// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {Dropdown} from 'semantic-ui-react';

import {getRandomColors} from 'indico/modules/events/timetable/colors';
import {SessionIcon} from 'indico/modules/events/timetable/SessionIcon';
import {FormFieldAdapter} from 'indico/react/forms';
import {FinalField} from 'indico/react/forms/fields';
import {Translate} from 'indico/react/i18n';

import {Colors, CompactSession, Session} from './types';

import './SessionSelect.module.scss';

const DEFAULT_DRAFT_ID = -1;

interface SessionOption {
  key: `session:${string}`;
  text: string | React.ReactNode;
  title: string;
  value: 'draft' | number;
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
      {title}
    </span>
  );
}

const _mapSessionToOption = (session: CompactSession): SessionOption => ({
  key: `session:${session.id}`,
  text: <DropdownElement title={session.title} colors={session.colors} />,
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
  const [query, setQuery] = useState('');
  const [options, setOptions] = useState<SessionOption[]>(_mapSessionsToOptions(sessions || []));

  const _onChangeValue = (id: number) => {
    const selectedSession = sessions.find(s => s.id === id);
    onChange(selectedSession);
  };

  const _sortOptionsFn = (a: SessionOption, b: SessionOption) =>
    a.title.toString().localeCompare(b.title.toString());

  const _createDraftSessionOption = () => {
    const newOptions = [...options];
    const draftSession: CompactSession = {
      id: DEFAULT_DRAFT_ID,
      title: query,
      colors: getRandomColors(),
    };
    const newSessionOption = _mapSessionToOption(draftSession);

    const draftSessionIndex = newOptions.findIndex(s => s.value === draftSession.id);
    if (draftSessionIndex !== -1) {
      newOptions[draftSessionIndex] = newSessionOption;
    } else {
      newOptions.push(newSessionOption);
    }

    setOptions(newOptions.toSorted(_sortOptionsFn));
    onChange(draftSession);
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
