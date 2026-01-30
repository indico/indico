// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import updateSpeakerProfileURL from 'indico-url:persons.api_speaker';
import speakersURL from 'indico-url:persons.api_speakers_list';

import React, {useCallback, useEffect, useMemo, useState} from 'react';
import ReactDOM from 'react-dom';
import {
  Button,
  Icon,
  Image,
  Popup,
  Search,
  Table,
  TableBody,
  TableCell,
  TableHeader,
  TableHeaderCell,
  TableRow,
} from 'semantic-ui-react';

import {
  EditSpeakerFormData,
  EditSpeakerProfile,
} from 'indico/modules/events/persons/EditSpeakerProfile';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import {Speaker} from './types';
import './Speakers.module.scss';

export function Speakers({eventId}: {eventId: number}) {
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const {data, reFetch} = useIndicoAxios(
    speakersURL({
      event_id: eventId,
    })
  );

  const [modalOpened, setModalOpened] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSpeaker, setSelectedSpeaker] = useState<Speaker>();
  const lowerCaseSearchTerm = useMemo(() => searchTerm.toLocaleLowerCase(), [searchTerm]);
  const filteredSpeakers = useMemo(
    () =>
      speakers
        ? speakers.filter(speaker => speaker.name.toLocaleLowerCase().includes(lowerCaseSearchTerm))
        : [],
    [lowerCaseSearchTerm, speakers]
  );

  const handleEditSpeaker = useCallback(
    async (formData: EditSpeakerFormData) => {
      const bodyFormData = new FormData();
      const photo = formData.photo?.['1']?.[0];
      if (photo !== undefined) {
        bodyFormData.append('photo', photo);
      }
      if (formData.description !== undefined) {
        bodyFormData.append('description', formData.description);
      }
      const config = {
        headers: {'content-type': 'multipart/form-data'},
      };
      try {
        const response = await indicoAxios.post(
          updateSpeakerProfileURL({event_id: eventId, person_id: selectedSpeaker.id}),
          bodyFormData,
          config
        );
        setModalOpened(false);
        setSpeakers(oldSpeakers => [
          ...oldSpeakers.filter(speaker => speaker.id !== selectedSpeaker.id),
          response.data,
        ]);
        reFetch();
      } catch (e) {
        handleAxiosError(e);
      }
    },
    [selectedSpeaker, eventId, reFetch]
  );

  useEffect(() => {
    setSpeakers(data);
  }, [data]);

  return (
    <>
      <div styleName="action-bar">
        <div styleName="action-bar-half">
          <Button>
            <Icon name="add" />
            {Translate.string('Add speakers')}
          </Button>
        </div>
        <div styleName="action-bar-half">
          <Search
            placeholder={Translate.string('Search speakers')}
            value={searchTerm}
            onSearchChange={(_, {value}) => setSearchTerm(value)}
            open={false}
            fluid
          />
        </div>
      </div>
      <Table sortable selectable singleLine fixed>
        <TableHeader>
          <TableRow>
            <TableHeaderCell disabled width={1} />
            <TableHeaderCell styleName="borderless" width={4}>
              {Translate.string('Name')}
            </TableHeaderCell>
            <TableHeaderCell width={4}>{Translate.string('Email')}</TableHeaderCell>
            <TableHeaderCell width={12}>{Translate.string('Description')}</TableHeaderCell>
            <TableHeaderCell disabled styleName="borderless" width={2} />
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredSpeakers.length > 0
            ? filteredSpeakers.map(speaker => (
                <TableRow key={speaker.id}>
                  <TableCell>
                    <Image src={speaker.speaker_photo_url ?? speaker.avatar_url} avatar />
                  </TableCell>
                  <TableCell>{speaker.name}</TableCell>
                  <TableCell>{speaker.email}</TableCell>
                  <TableCell>{speaker.speaker_description}</TableCell>
                  <TableCell>
                    <Popup
                      content={Translate.string('Edit speaker profile')}
                      position="top center"
                      trigger={
                        <Icon
                          name="edit"
                          link
                          color="black"
                          onClick={() => {
                            setSelectedSpeaker(speaker);
                            setModalOpened(true);
                          }}
                        />
                      }
                    />
                    <Popup
                      content={Translate.string('Delete speaker profile')}
                      position="top center"
                      trigger={<Icon name="trash" link color="black" onClick={() => null} />}
                    />
                  </TableCell>
                </TableRow>
              ))
            : null}
        </TableBody>
      </Table>
      {filteredSpeakers.length === 0 ? (
        searchTerm.length > 0 ? (
          <p>There are no entries that match your search criteria.</p>
        ) : (
          <p>There are no speakers yet.</p>
        )
      ) : null}
      {modalOpened && (
        <EditSpeakerProfile
          onClose={() => {
            setModalOpened(false);
            setSelectedSpeaker(undefined);
          }}
          onSubmit={handleEditSpeaker}
          speaker={selectedSpeaker}
          eventId={eventId}
        />
      )}
    </>
  );
}

customElements.define(
  'ind-speakers',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(<Speakers eventId={JSON.parse(this.getAttribute('event-id'))} />, this);
    }
  }
);
