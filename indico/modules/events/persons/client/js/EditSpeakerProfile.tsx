// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadSpeakerPhoto from 'indico-url:persons.upload_speaker_photo';

import React, {useState} from 'react';
import {useForm} from 'react-final-form';
import {Dropdown, Icon, Popup, SemanticICONS} from 'semantic-ui-react';

import {FinalSingleFileManager} from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

import './EditSpeakerProfile.module.scss';
import {Speaker} from './types';

export interface EditSpeakerFormData {
  description?: string;
  github?: string;
  facebook?: string;
  linkedin?: string;
  webpage?: string;
  photo?: string;
}

interface EditSpeakerProfileProps {
  speaker?: Speaker;
  eventId: number;
  onClose?: () => void;
  onSubmit?: (formData: EditSpeakerFormData) => void;
}

type ExtraField = 'github' | 'facebook' | 'linkedin' | 'webpage';

const FIELD_TITLES: Record<ExtraField, string> = {
  facebook: 'Facebook',
  linkedin: 'LinkedIn',
  github: 'GitHub',
  webpage: 'Webpage',
};

const FIELD_ICONS: Record<ExtraField, SemanticICONS> = {
  facebook: 'facebook',
  linkedin: 'linkedin',
  github: 'github',
  webpage: 'world',
};

function getExistingExtraFields(speaker: Speaker) {
  const fields: ExtraField[] = [];
  if (speaker.speaker_facebook !== null && speaker.speaker_facebook !== '') {
    fields.push('facebook');
  }
  if (speaker.speaker_linkedin !== null && speaker.speaker_linkedin !== '') {
    fields.push('linkedin');
  }
  if (speaker.speaker_github !== null && speaker.speaker_github !== '') {
    fields.push('github');
  }
  if (speaker.speaker_webpage !== null && speaker.speaker_webpage !== '') {
    fields.push('webpage');
  }
  return fields;
}

function EditSpeakerProfileForm({speaker, eventId}: {speaker: Speaker; eventId: number}) {
  const [extraFields, setExtraFields] = useState<ExtraField[]>(getExistingExtraFields(speaker));
  const form = useForm();

  return (
    <>
      <FinalSingleFileManager
        name="photo"
        label={Translate.string('Profile Picture')}
        uploadURL={uploadSpeakerPhoto({event_id: eventId, person_id: speaker.id})}
        mustChange
      />
      <FinalTextArea
        name="description"
        label={Translate.string('Description')}
        initialValue={speaker.speaker_description}
      />
      {extraFields.map(name => (
        <div styleName="row" key={name}>
          <FinalInput
            name={name}
            label={
              <p>
                {FIELD_TITLES[name]} <Icon name={FIELD_ICONS[name]} />
              </p>
            }
            initialValue={speaker[`speaker_${name}`]}
          />
          <Popup
            content={Translate.string('Remove link')}
            position="right center"
            trigger={
              <Icon
                name="trash"
                link
                color="black"
                onClick={() => {
                  setExtraFields(old => old.filter(field => field !== name));
                  speaker[`speaker_${name}`] = null;
                  form.change(name, undefined);
                }}
              />
            }
          />
        </div>
      ))}
      {extraFields.length < Object.keys(FIELD_TITLES).length && (
        <div styleName="centered-field">
          <Dropdown
            text={Translate.string('Add link')}
            icon="add"
            floating
            labeled
            button
            className="icon"
          >
            <Dropdown.Menu>
              <Dropdown.Header content={Translate.string('Select the link type')} />
              <Dropdown.Divider />
              {Object.entries(FIELD_TITLES)
                .filter(entry => !extraFields.includes(entry[0] as ExtraField))
                .map(([name, title]: [ExtraField, string]) => (
                  <Dropdown.Item
                    key={name}
                    icon={FIELD_ICONS[name]}
                    text={title}
                    onClick={() => setExtraFields(old => [...old, name])}
                  />
                ))}
            </Dropdown.Menu>
          </Dropdown>
        </div>
      )}
    </>
  );
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
      <EditSpeakerProfileForm speaker={speaker} eventId={eventId} />
    </FinalModalForm>
  );
}
