// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import speakersURL from 'indico-url:persons.api_speakers_list';

import React, {useEffect, useMemo, useState} from 'react';
import ReactDOM from 'react-dom';
import {Icon, Divider} from 'semantic-ui-react';

import {useIndicoAxios} from 'indico/react/hooks';

import {Speaker} from './types';

import './SpeakersDisplay.module.scss';

function SpeakerProfile({speaker}: {speaker: Speaker}) {
  return (
    <div styleName="profile-container">
      <div styleName="profile-header">
        <h4>
          {speaker.name} {speaker.affiliation ? ` | ${speaker.affiliation}` : ''}
        </h4>
        <div styleName="socials">
          {speaker.speaker_facebook && (
            <a href={speaker.speaker_facebook} rel="noreferrer">
              <Icon name="facebook" size="large" />
            </a>
          )}
          {speaker.speaker_github && (
            <a href={speaker.speaker_github} rel="noreferrer">
              <Icon name="github" size="large" />
            </a>
          )}
          {speaker.speaker_linkedin && (
            <a href={speaker.speaker_linkedin} rel="noreferrer">
              <Icon name="linkedin" size="large" />
            </a>
          )}
          {speaker.speaker_webpage && (
            <a href={speaker.speaker_webpage} rel="noreferrer">
              <Icon name="world" size="large" />
            </a>
          )}
        </div>
      </div>
      <img src={speaker.speaker_photo_url ?? speaker.avatar_url} styleName="speaker-photo" />
      <div>
        {speaker.speaker_description.split('\n').map((line, index) => (
          // eslint-disable-next-line react/no-array-index-key
          <p key={index}>{line}</p>
        ))}
      </div>
    </div>
  );
}

export function SpeakersDisplay({eventId}: {eventId: number}) {
  const [speakers, setSpeakers] = useState<Speaker[]>([]);
  const {data} = useIndicoAxios(
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
              speaker.speaker_photo_url !== null
          )
        : [],
    [speakers]
  );

  useEffect(() => {
    setSpeakers(data);
  }, [data]);

  return (
    <div>
      {speakersWithProfile.map((speaker, index) => (
        <div key={speaker.id}>
          <SpeakerProfile key={speaker.id} speaker={speaker} />
          {index < speakersWithProfile.length - 1 && <Divider />}
        </div>
      ))}
    </div>
  );
}

customElements.define(
  'ind-speakers-display',
  class extends HTMLElement {
    connectedCallback() {
      ReactDOM.render(
        <SpeakersDisplay eventId={JSON.parse(this.getAttribute('event-id'))} />,
        this
      );
    }
  }
);
