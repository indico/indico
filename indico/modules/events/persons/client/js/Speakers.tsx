// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import updateSpeakerProfileURL from 'indico-url:persons.api_speaker_profile';
import speakersURL from 'indico-url:persons.api_speakers_list';

import React, {useCallback, useEffect, useMemo, useState} from 'react';
import ReactDOM from 'react-dom';
import {Button, Icon, Image, Popup, Search, Table} from 'semantic-ui-react';

import {
  EditSpeakerFormData,
  EditSpeakerProfile,
} from 'indico/modules/events/persons/EditSpeakerProfile';
import {SpeakerSearch} from 'indico/modules/events/persons/SpeakerSearch';
import {handleSubmitError} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

import {Speaker} from './types';
import './Speakers.module.scss';

type SpeakersModalName = 'SEARCH_SPEAKER' | 'EDIT_SPEAKER';

export function Speakers({eventId}: {eventId: number}) {
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const {data, reFetch} = useIndicoAxios(
    speakersURL({
      event_id: eventId,
    })
  );
  const speakersWithProfile = useMemo(
    () =>
      speakers
        ? speakers.filter(
            speaker =>
              (speaker.speaker_description !== null && speaker.speaker_description !== '') ||
              (speaker.speaker_facebook !== null && speaker.speaker_facebook !== '') ||
              (speaker.speaker_github !== null && speaker.speaker_github !== '') ||
              (speaker.speaker_linkedin !== null && speaker.speaker_linkedin !== '') ||
              (speaker.speaker_webpage !== null && speaker.speaker_webpage !== '') ||
              speaker.speaker_photo_url !== null
          )
        : [],
    [speakers]
  );
  const speakerIDsWithProfile = useMemo(
    () => speakersWithProfile.map(speaker => speaker.id),
    [speakersWithProfile]
  );
  const speakersWithoutProfile = useMemo(() => {
    return speakers ? speakers.filter(speaker => !speakerIDsWithProfile.includes(speaker.id)) : [];
  }, [speakers, speakerIDsWithProfile]);

  const [openedModal, setOpenedModal] = useState<SpeakersModalName | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSpeaker, setSelectedSpeaker] = useState<Speaker>();
  const lowerCaseSearchTerm = useMemo(() => searchTerm.toLocaleLowerCase(), [searchTerm]);
  const filteredSpeakers = useMemo(
    () =>
      speakersWithProfile.filter(speaker =>
        speaker.name.toLocaleLowerCase().includes(lowerCaseSearchTerm)
      ),
    [lowerCaseSearchTerm, speakersWithProfile]
  );

  const handleEditSpeaker = useCallback(
    async (formData: EditSpeakerFormData) => {
      const bodyFormData = new FormData();
      console.log(formData);
      if (formData.photo !== undefined) {
        bodyFormData.append('photo', formData.photo);
      }
      if (formData.description !== undefined) {
        bodyFormData.append('description', formData.description);
      }
      if (formData.github !== undefined) {
        bodyFormData.append('github', formData.github);
      }
      if (formData.facebook !== undefined) {
        bodyFormData.append('facebook', formData.facebook);
      }
      if (formData.linkedin !== undefined) {
        bodyFormData.append('linkedin', formData.linkedin);
      }
      if (formData.webpage !== undefined) {
        bodyFormData.append('webpage', formData.webpage);
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
        setOpenedModal(null);
        setSpeakers(oldSpeakers => [
          ...oldSpeakers.filter(speaker => speaker.id !== selectedSpeaker.id),
          response.data,
        ]);
        reFetch();
      } catch (e) {
        return handleSubmitError(e);
      }
    },
    [selectedSpeaker, eventId, reFetch]
  );

  const handleDeleteSpeaker = useCallback(
    async (speakerId: number) => {
      await indicoAxios.delete(updateSpeakerProfileURL({event_id: eventId, person_id: speakerId}));
      setSpeakers(old =>
        old.map(speaker =>
          speaker.id === speakerId
            ? {...speaker, speaker_description: null, speaker_photo_url: null}
            : speaker
        )
      );
      reFetch();
    },
    [reFetch, eventId]
  );

  useEffect(() => {
    setSpeakers(data);
  }, [data]);

  return (
    <>
      <div styleName="action-bar">
        <div styleName="action-bar-half">
          <Button
            icon="add"
            content={Translate.string('Add speaker profile')}
            onClick={() => setOpenedModal('SEARCH_SPEAKER')}
          />
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
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell disabled width={1} />
            <Table.HeaderCell styleName="borderless" width={4}>
              {Translate.string('Name')}
            </Table.HeaderCell>
            <Table.HeaderCell width={4}>{Translate.string('Email')}</Table.HeaderCell>
            <Table.HeaderCell width={12}>{Translate.string('Description')}</Table.HeaderCell>
            <Table.HeaderCell disabled styleName="borderless" width={2} />
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {filteredSpeakers.length > 0
            ? filteredSpeakers.map(speaker => (
                <Table.Row key={speaker.id}>
                  <Table.Cell>
                    <Image src={speaker.speaker_photo_url ?? speaker.avatar_url} avatar />
                  </Table.Cell>
                  <Table.Cell>{speaker.name}</Table.Cell>
                  <Table.Cell>{speaker.email}</Table.Cell>
                  <Table.Cell>{speaker.speaker_description}</Table.Cell>
                  <Table.Cell>
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
                            setOpenedModal('EDIT_SPEAKER');
                          }}
                        />
                      }
                    />
                    <Popup
                      content={Translate.string('Delete speaker profile')}
                      position="top center"
                      trigger={
                        <Icon
                          name="trash"
                          link
                          color="black"
                          onClick={() => handleDeleteSpeaker(speaker.id)}
                        />
                      }
                    />
                  </Table.Cell>
                </Table.Row>
              ))
            : null}
        </Table.Body>
      </Table>
      {filteredSpeakers.length === 0 ? (
        searchTerm.length > 0 ? (
          <p>
            <Translate>There are no entries that match your search criteria.</Translate>
          </p>
        ) : (
          <p>
            <Translate>There are no speaker profiles yet.</Translate>
          </p>
        )
      ) : null}
      {openedModal === 'EDIT_SPEAKER' && (
        <EditSpeakerProfile
          onClose={() => {
            setOpenedModal(null);
            setSelectedSpeaker(undefined);
          }}
          onSubmit={handleEditSpeaker}
          speaker={selectedSpeaker}
          eventId={eventId}
        />
      )}
      {openedModal === 'SEARCH_SPEAKER' && (
        <SpeakerSearch
          onClose={() => {
            setOpenedModal(null);
          }}
          onSubmit={speaker => {
            setSelectedSpeaker(speaker);
            setOpenedModal('EDIT_SPEAKER');
          }}
          speakers={speakersWithoutProfile}
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
