// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadSpeakerPhoto from 'indico-url:persons.upload_speaker_photo';

import React, {useMemo, useState} from 'react';
import {Icon, SemanticICONS} from 'semantic-ui-react';

import {FinalPictureManager} from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

import {Speaker, SpeakerLink} from './types';

import './EditSpeakerProfile.module.scss';

export const DEFAULT_SOCIAL_ICONS: Record<string, SemanticICONS> = {
  Facebook: 'facebook',
  LinkedIn: 'linkedin',
  GitHub: 'github',
  Webpage: 'world',
};

export interface EditSpeakerFormData {
  description?: string;
  speaker_links?: {id: number; url: string}[];
  photo?: string;
}

interface EditSpeakerProfileProps {
  speaker: Speaker;
  eventId: number;
  onClose: () => void;
  onSubmit: (formData: EditSpeakerFormData) => void;
  speakerLinks: SpeakerLink[];
}

function EditSpeakerProfileForm({
  speaker,
  eventId,
  speakerLinks,
}: {
  speaker: Speaker;
  eventId: number;
  speakerLinks: SpeakerLink[];
}) {
  const [displayInitialPicture, setDisplayInitialPicture] = useState(true);
  const speakerLinkValues = useMemo(() => {
    return speakerLinks.map(link => {
      const linkWithValue = speaker.speaker_links.find(l => l.id === link.id);
      return {...link, url: linkWithValue?.value ?? ''};
    });
  }, [speakerLinks, speaker.speaker_links]);

  return (
    <>
      <FinalPictureManager
        name="photo"
        label={Translate.string('Profile Picture')}
        uploadURL={uploadSpeakerPhoto({event_id: eventId, person_id: speaker.id})}
        previewURL={speaker.speaker_photo_url}
        initialPictureDetails={
          displayInitialPicture ? {uuid: '', filename: '', size: 0} : undefined
        }
        onChange={(v: string | null) => {
          if (v === null) {
            // clearing picture should make it so the initial picture is not displayed
            setDisplayInitialPicture(false);
          }
        }}
        required={false}
      />
      <FinalTextArea
        name="description"
        nullIfEmpty={false}
        label={Translate.string('Description')}
        initialValue={speaker.speaker_description}
      />
      {speakerLinkValues.map((link, index) => (
        <div styleName="row" key={link.id}>
          <FinalInput
            name={`speaker_links.${index}.url`}
            label={
              <p>
                {link.name} {link.icon && <Icon name={link.icon as SemanticICONS} />}
              </p>
            }
            initialValue={link.url}
          />
          <br />
        </div>
      ))}
    </>
  );
}

export function EditSpeakerProfile({
  onClose,
  onSubmit,
  speaker,
  eventId,
  speakerLinks,
}: EditSpeakerProfileProps) {
  return (
    <FinalModalForm
      id="edit-speaker-form"
      onClose={onClose}
      onSubmit={onSubmit}
      disabledUntilChange={false}
      size="large"
      initialValues={{speaker_links: speakerLinks.map(link => ({id: link.id}))}}
      header={
        speaker.has_speaker_profile
          ? Translate.string('Edit Speaker Profile')
          : Translate.string('Create Speaker Profile')
      }
    >
      <EditSpeakerProfileForm speaker={speaker} eventId={eventId} speakerLinks={speakerLinks} />
    </FinalModalForm>
  );
}
