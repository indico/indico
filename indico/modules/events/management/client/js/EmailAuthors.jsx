// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import abstractsPersonListURL from 'indico-url:abstracts.person_list';
import contribsPersonListURL from 'indico-url:contributions.person_list';
import sessionsPersonListURL from 'indico-url:sessions.person_list';

import PropTypes from 'prop-types';
import React, {useEffect, useMemo, useState} from 'react';
import {Button, Dimmer, Loader, Message, Modal} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import {EmailParticipantRolesButton} from 'indico/modules/events/persons/EmailParticipantRolesButton';
import {getIds} from 'indico/modules/events/persons/util';

import PersonList from './PersonList';

// In abstracts there is always a submitter so we don't need an emptyListMessage
const CONTEXTS = {
  abstract: {personListURL: abstractsPersonListURL},
  contribution: {
    personListURL: contribsPersonListURL,
    emptyListMessage: Translate.string(
      'There are no persons associated with the selected contributions'
    ),
  },
  session: {
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
    contexts: ['abstract'],
  },
  speaker: {
    text: Translate.string('Speakers'),
    isMatch: person => person.speaker,
  },
  primaryAuthor: {
    text: Translate.string('Primary authors'),
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

export function EmailAuthorsButton({eventId, context, paramsSelector, triggerSelector}) {
  const [open, setOpen] = useState(false);
  const sourceIds = getIds(paramsSelector);

  useEffect(() => {
    if (!triggerSelector) {
      return;
    }
    const handler = () => setOpen(true);
    const element = document.querySelector(triggerSelector);
    element.addEventListener('click', handler);
    return () => element.removeEventListener('click', handler);
  }, [triggerSelector]);

  return (
    open && (
      <EmailAuthorsModal
        eventId={eventId}
        sourceIds={sourceIds}
        context={context}
        onClose={() => setOpen(false)}
      />
    )
  );
}

EmailAuthorsButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  context: PropTypes.oneOf(Object.keys(CONTEXTS)).isRequired,
  paramsSelector: PropTypes.string.isRequired,
  triggerSelector: PropTypes.string.isRequired,
};

function EmailAuthorsModal({eventId, sourceIds, context, onClose}) {
  const [selectedPersons, setSelectedPersons] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [successMessage, setSuccessMessage] = useState(undefined);
  const [activeFilters, setActiveFilters] = useState([]);
  const formData = new FormData();
  sourceIds.forEach(v => formData.append(`${context}_id`, v));
  const {data, loading} = useIndicoAxios(
    {
      url: CONTEXTS[context].personListURL({event_id: eventId}),
      method: 'POST',
      data: formData,
      headers: {'content-type': 'multipart/form-data'},
    },
    {camelize: true}
  );
  const eventPersons = useMemo(() => new Map(data?.eventPersons.map(p => [p.id, p])), [data]);
  const extraRoles =
    context === 'abstract'
      ? [
          {
            icon: 'user-check icon',
            isActive: p => p.submitter,
            titleActive: Translate.string('This person submitted an abstract'),
            titleInactive: Translate.string("This person hasn't submitted any abstracts"),
          },
        ]
      : undefined;

  const onChangeSelection = ({person, user}) => {
    person && setSelectedPersons(person);
    user && setSelectedUsers(user);
  };

  const isVisible = person =>
    !activeFilters.length || activeFilters.every(filter => FILTER_OPTIONS[filter].isMatch(person));

  const toggleFilter = name => {
    setActiveFilters(
      activeFilters.includes(name)
        ? activeFilters.filter(f => f !== name)
        : [...activeFilters, name]
    );
  };

  const filterButtons = Object.entries(FILTER_OPTIONS)
    .filter(([, filter]) => !filter.contexts || filter.contexts.includes(context))
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
        {successMessage}
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
        ) : eventPersons.size ? (
          <PersonList
            persons={data.eventPersons}
            selectedPersons={selectedPersons}
            selectedUsers={selectedUsers}
            onChangeSelection={onChangeSelection}
            isSelectable={person => !!person.email}
            isVisible={isVisible}
            extraRoles={extraRoles}
          />
        ) : (
          <Message error>{CONTEXTS[context].emptyListMessage}</Message>
        )}
      </Modal.Content>
      <Modal.Actions>
        <EmailParticipantRolesButton
          eventId={eventId}
          personIds={selectedPersons.filter(id => isVisible(eventPersons.get(id)))}
          userIds={selectedUsers.filter(id => isVisible(eventPersons.get(id)))}
          // onSuccess={msg => setSuccessMessage(msg)}
          primary
        />
        <Translate as={Button} onClick={() => onClose()}>
          Close
        </Translate>
      </Modal.Actions>
    </Modal>
  );
}

EmailAuthorsModal.propTypes = {
  eventId: PropTypes.number.isRequired,
  sourceIds: PropTypes.arrayOf(PropTypes.number).isRequired,
  context: PropTypes.oneOf(Object.keys(CONTEXTS)).isRequired,
  onClose: PropTypes.func.isRequired,
};
