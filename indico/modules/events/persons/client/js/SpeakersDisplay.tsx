// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import speakersURL from 'indico-url:persons.api_speakers_list';

import React, {useEffect, useMemo, useState} from 'react';
import ReactDOM from 'react-dom';
import {Icon, Divider, SemanticICONS} from 'semantic-ui-react';

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
          {Object.entries(speaker.speaker_socials ?? {}).map(([socialName, socialInfo]) => (
            <a href={socialInfo.url} rel="noreferrer" key={socialName}>
              <Icon name={socialInfo.icon as SemanticICONS} size="large" title={socialName} />
            </a>
          ))}
        </div>
      </div>
      <div styleName="speaker-content-body">
        <img src={speaker.speaker_photo_url} styleName="speaker-photo" />
        <div>
          {(speaker.speaker_description ?? '').split('\n').map((line, index) => (
            // eslint-disable-next-line react/no-array-index-key
            <p key={index}>{line}</p>
          ))}
        </div>
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
    () => (speakers ? speakers.filter(speaker => speaker.has_speaker_profile) : []),
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
        <SpeakersDisplay eventId={JSON.parse(this.getAttribute('event-id') ?? '')} />,
        this
      );
    }
  }
);
