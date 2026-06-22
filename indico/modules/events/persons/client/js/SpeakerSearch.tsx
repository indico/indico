// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useMemo, useState} from 'react';
import {Button, Modal, Search, Table} from 'semantic-ui-react';

import {Translate} from 'indico/react/i18n';

import './Speakers.module.scss';
import {Speaker} from './types';

interface SpeakerSearchProps {
  speakers: Speaker[];
  onClose?: () => void;
  onSubmit?: (speaker: Speaker) => void;
}

function matchesSearchTerm(speaker: Speaker, search: string) {
  const lowercaseSearch = search.toLocaleLowerCase();
  if (speaker.name.toLocaleLowerCase().includes(lowercaseSearch)) {
    return true;
  }
  if (speaker.email.toLocaleLowerCase().includes(lowercaseSearch)) {
    return true;
  }
  if (speaker.affiliation.toLocaleLowerCase().includes(lowercaseSearch)) {
    return true;
  }
  return false;
}

export function SpeakerSearch({onClose, onSubmit, speakers}: SpeakerSearchProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const filteredSpeakers = useMemo(
    () => speakers.filter(speaker => matchesSearchTerm(speaker, searchTerm)),
    [searchTerm, speakers]
  );
  const [selectedSpeaker, setSelectedSpeaker] = useState<Speaker | null>(null);

  return (
    <Modal open onClose={onClose} onSubmit={onSubmit} closeIcon>
      <Translate as={Modal.Header}>Speaker Search</Translate>
      <Modal.Content>
        <div>
          <div styleName="action-bar">
            <Translate as={Modal.Description}>Select a speaker from the list below:</Translate>
            <Search
              placeholder={Translate.string('Search')}
              value={searchTerm}
              onSearchChange={(_, {value}) => setSearchTerm(value)}
              open={false}
              fluid
            />
          </div>
          <Table singleLine fixed selectable>
            <Table.Header>
              <Table.Row>
                <Table.HeaderCell width={3}>
                  <Translate>Name</Translate>
                </Table.HeaderCell>
                <Table.HeaderCell width={5}>
                  <Translate>Email</Translate>
                </Table.HeaderCell>
                <Table.HeaderCell width={3}>
                  <Translate>Affiliation</Translate>
                </Table.HeaderCell>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {filteredSpeakers.length > 0
                ? filteredSpeakers.map(speaker => (
                    <Table.Row
                      key={speaker.id}
                      active={speaker.id === selectedSpeaker?.id}
                      styleName="clickable"
                      onClick={() =>
                        selectedSpeaker?.id === speaker.id
                          ? setSelectedSpeaker(null)
                          : setSelectedSpeaker(speaker)
                      }
                    >
                      <Table.Cell>{speaker.name}</Table.Cell>
                      <Table.Cell>{speaker.email}</Table.Cell>
                      <Table.Cell>{speaker.affiliation}</Table.Cell>
                    </Table.Row>
                  ))
                : null}
            </Table.Body>
          </Table>
          {speakers.length === 0 && (
            <p>
              <Translate>There are no speakers to choose from.</Translate>
            </p>
          )}
          {speakers.length > 0 && filteredSpeakers.length === 0 && (
            <p>
              <Translate>There are no entries that match your search criteria.</Translate>
            </p>
          )}
        </div>
      </Modal.Content>
      <Modal.Actions>
        <Button
          onClick={() => onSubmit(selectedSpeaker)}
          primary
          disabled={selectedSpeaker === null}
        >
          <Translate>Confirm</Translate>
        </Button>
        <Button onClick={onClose}>
          <Translate>Close</Translate>
        </Button>
      </Modal.Actions>
    </Modal>
  );
}
