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
import React, {useEffect, useState} from 'react';
import {Button, Dimmer, Loader, Message, Modal} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

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

// TODO: turn into util?
// TODO: now do we need to check offsetwidth/height?
const getIds = selector =>
  Array.from(document.querySelectorAll(selector))
    .filter(e => e.offsetWidth > 0 || e.offsetHeight > 0)
    .map(e => +e.value);

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

export function EmailAuthorsModal({eventId, sourceIds, context, onClose}) {
  const [selectedPersons, setSelectedPersons] = useState([]);
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

  return (
    <Modal open onClose={() => onClose()} size="large">
      <Modal.Header content={Translate.string('Email authors')} />
      <Modal.Content>
        {loading || !data ? (
          <Dimmer active>
            <Loader />
          </Dimmer>
        ) : data.eventPersons.length ? (
          <PersonList
            persons={data.eventPersons}
            selectedPersons={selectedPersons}
            onSelect={newSelected => setSelectedPersons(newSelected)}
            isSelectable={person => !!person.email}
            extraRoles={extraRoles}
          />
        ) : (
          <Message error>{CONTEXTS[context].emptyListMessage}</Message>
        )}
      </Modal.Content>
      <Modal.Actions>
        <Button onClick={() => onClose()}>
          <Translate>Close</Translate>
        </Button>
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
