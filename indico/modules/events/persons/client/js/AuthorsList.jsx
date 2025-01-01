// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import abstractsPersonListURL from 'indico-url:abstracts.person_list';
import contribsPersonListURL from 'indico-url:contributions.person_list';
import sessionsPersonListURL from 'indico-url:sessions.person_list';

import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {Button, Dimmer, Loader, Message, Modal} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import {EmailSentMessage} from './EmailDialog';
import {EmailParticipantRolesButton} from './EmailParticipantRolesButton';
import PersonList from './PersonList';

// In abstracts there is always a submitter so we don't need an emptyListMessage
export const CONTEXTS = {
  abstracts: {idType: 'abstract_id', personListURL: abstractsPersonListURL},
  contributions: {
    idType: 'contribution_id',
    personListURL: contribsPersonListURL,
    emptyListMessage: Translate.string(
      'There are no persons associated with the selected contributions'
    ),
  },
  sessions: {
    idType: 'session_id',
    personListURL: sessionsPersonListURL,
    emptyListMessage: Translate.string(
      'There are no persons associated with contributions in the selected sessions'
    ),
  },
};

const FILTER_OPTIONS = {
  submitter: {
    text: Translate.string('Submitters'),
    isMatch: person => person.submitter,
    contexts: ['abstracts'],
  },
  speaker: {
    text: Translate.string('Speakers'),
    isMatch: person => person.speaker,
  },
  primaryAuthor: {
    text: Translate.string('Authors'),
    isMatch: person => person.primaryAuthor,
  },
  secondaryAuthor: {
    text: Translate.string('Co-authors'),
    isMatch: person => person.secondaryAuthor,
  },
  notRegistered: {
    text: Translate.string('Not registered'),
    isMatch: person => !person.registered,
  },
};

export function AuthorsList({eventId, sourceIds, objectContext, onClose}) {
  const [selectedPersons, setSelectedPersons] = useState([]);
  const [sentEmailCount, setSentEmailCount] = useState(undefined);
  const [activeFilters, setActiveFilters] = useState([]);
  const formData = new FormData();
  sourceIds.forEach(v => formData.append(CONTEXTS[objectContext].idType, v));
  const {data, loading} = useIndicoAxios(
    {
      url: CONTEXTS[objectContext].personListURL({event_id: eventId}),
      method: 'POST',
      data: formData,
      headers: {'content-type': 'multipart/form-data'},
    },
    {camelize: true}
  );
  const extraRoles =
    objectContext === 'abstracts'
      ? [
          {
            icon: 'user-check icon',
            isActive: p => p.submitter,
            titleActive: Translate.string('This person submitted an abstract'),
            titleInactive: Translate.string("This person hasn't submitted any abstracts"),
          },
        ]
      : undefined;

  const isVisible = person =>
    !activeFilters.length || activeFilters.some(filter => FILTER_OPTIONS[filter].isMatch(person));

  const toggleFilter = name => {
    setActiveFilters(
      activeFilters.includes(name)
        ? activeFilters.filter(f => f !== name)
        : [...activeFilters, name]
    );
  };

  const filterButtons = Object.entries(FILTER_OPTIONS)
    .filter(([, filter]) => !filter.contexts || filter.contexts.includes(objectContext))
    .map(([name, filter]) => ({
      key: name,
      content: filter.text,
      onClick: () => toggleFilter(name),
      primary: activeFilters.includes(name),
    }));

  return (
    <Modal open onClose={() => onClose()} size="large">
      <Modal.Header content={Translate.string('Authors list')} />
      <Modal.Content>
        {sentEmailCount && <EmailSentMessage count={sentEmailCount} />}
        <div>
          <Translate
            as="div"
            style={{display: 'inline-block', fontWeight: 'bold', padding: '0.5em'}}
          >
            Filter by
          </Translate>
          <Button.Group buttons={filterButtons} compact />
        </div>
        {loading || !data ? (
          <Dimmer active>
            <Loader />
          </Dimmer>
        ) : Object.keys(data.eventPersons).length ? (
          <PersonList
            persons={Object.values(data.eventPersons)}
            selectedPersons={selectedPersons}
            onChangeSelection={persons => setSelectedPersons(persons)}
            isSelectable={person => !!person.email}
            isVisible={isVisible}
            extraRoles={extraRoles}
          />
        ) : (
          <Message error>{CONTEXTS[objectContext].emptyListMessage}</Message>
        )}
      </Modal.Content>
      <Modal.Actions>
        <EmailParticipantRolesButton
          eventId={eventId}
          persons={selectedPersons.filter(id => isVisible(data.eventPersons[id]))}
          onSubmitSucceeded={count => setSentEmailCount(count)}
          successTimeout={0}
          primary
        />
        <Translate as={Button} onClick={() => onClose()}>
          Close
        </Translate>
      </Modal.Actions>
    </Modal>
  );
}

AuthorsList.propTypes = {
  eventId: PropTypes.number.isRequired,
  sourceIds: PropTypes.arrayOf(PropTypes.number).isRequired,
  objectContext: PropTypes.oneOf(Object.keys(CONTEXTS)).isRequired,
  onClose: PropTypes.func.isRequired,
};
