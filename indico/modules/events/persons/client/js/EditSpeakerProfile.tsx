// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadSpeakerPhoto from 'indico-url:persons.upload_speaker_photo';

import React from 'react';

import {FinalFileManager} from 'indico/modules/events/editing/editing/timeline/FileManager';
import {FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

import './EditSpeakerProfile.module.scss';
import {Speaker} from './types';

export interface EditSpeakerFormData {
  description?: string;
  photo?: FileList;
}

interface EditSpeakerProfileProps {
  speaker?: Speaker;
  eventId: number;
  onClose?: () => void;
  onSubmit?: (formData: EditSpeakerFormData) => void;
}

export function EditSpeakerProfile({onClose, onSubmit, speaker, eventId}: EditSpeakerProfileProps) {
  return (
    <FinalModalForm
      id="edit-speaker-form"
      onClose={onClose}
      onSubmit={onSubmit}
      disabledUntilChange={false}
      header={
        speaker
          ? Translate.string('Edit Speaker Profile')
          : Translate.string('Create Speaker Profile')
      }
    >
      <div styleName="centered-field">
        <FinalFileManager
          name="photo"
          fileTypes={[
            {
              name: Translate.string('Speaker Photo'),
              id: 1,
              extensions: ['png', 'jpg', ' jpeg'],
              allowMultipleFiles: false,
              filenamePattern: '',
            },
          ]}
          uploadURL={uploadSpeakerPhoto({event_id: eventId, person_id: speaker.id})}
          mustChange={false}
        />
      </div>
      <FinalTextArea
        name="description"
        label={Translate.string('Description')}
        initialValue={speaker.speaker_description}
      />
    </FinalModalForm>
  );
}
