// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadSpeakerPhoto from 'indico-url:persons.upload_speaker_photo';

import React, {useCallback, useEffect, useState} from 'react';
import {useForm} from 'react-final-form';
import {Dropdown, Icon, Popup, SemanticICONS} from 'semantic-ui-react';
import * as SUI from 'semantic-ui-react/dist/es/lib/SUI';

import {FinalPictureManager} from 'indico/react/components';
import {FinalDropdown, FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalModalForm} from 'indico/react/forms/final-form';
import {Translate} from 'indico/react/i18n';

import {Speaker} from './types';

import './EditSpeakerProfile.module.scss';

export const DEFAULT_SOCIAL_ICONS: Record<string, SemanticICONS> = {
  Facebook: 'facebook',
  LinkedIn: 'linkedin',
  GitHub: 'github',
  Webpage: 'world',
};

export const DEFAULT_SOCIAL_TITLES = ['Facebook', 'LinkedIn', 'GitHub', 'Webpage'];

export interface EditSpeakerFormData {
  description?: string;
  socials?: Record<
    string,
    {
      url: string;
      icon?: string;
    }
  >;
  photo?: string;
}

interface EditSpeakerProfileProps {
  speaker: Speaker;
  eventId: number;
  onClose: () => void;
  onSubmit: (formData: EditSpeakerFormData) => void;
}

interface AddSocialFormData {
  title: string;
  icon?: string;
}

function makeTitle(s: string) {
  return s
    .split(' ')
    .map(word =>
      word.length === 0 ? word : word.charAt(0).toLocaleUpperCase() + word.substring(1)
    )
    .join(' ');
}

const ICON_OPTIONS = SUI.ICONS_AND_ALIASES.map((iconName: string) => ({
  key: iconName,
  value: iconName,
  icon: iconName,
  text: makeTitle(iconName),
}));

function EditSpeakerProfileForm({speaker, eventId}: {speaker: Speaker; eventId: number}) {
  const [speakerSocials, setSpeakerSocials] = useState(speaker.speaker_socials ?? {});
  const [customSocialModalOpened, setCustomSocialModalOpened] = useState(false);
  const [displayInitialPicture, setDisplayInitialPicture] = useState(true);

  const form = useForm();

  const openCustomSocialModal = useCallback(() => setCustomSocialModalOpened(true), []);
  const closeCustomSocialModal = useCallback(() => setCustomSocialModalOpened(false), []);

  const addSpeakerSocial = useCallback((name: string, icon?: string) => {
    setSpeakerSocials(old => ({...old, [name]: {url: '', icon}}));
  }, []);

  const addSocial = useCallback(
    (formData: AddSocialFormData) => {
      addSpeakerSocial(formData.title, formData.icon);
      closeCustomSocialModal();
    },
    [closeCustomSocialModal, addSpeakerSocial]
  );

  useEffect(() => {
    // Keep `icon` property in sync
    const unsubscribe = form.subscribe(
      formState => {
        const socials: {url: string; icon?: string}[] | undefined = formState.values.socials;
        if (socials === undefined) {
          return;
        }
        for (const [name, value] of Object.entries(socials)) {
          if (value.icon === undefined && speakerSocials[name].icon !== undefined) {
            form.change(`socials.${name}.icon`, speakerSocials[name].icon);
          }
        }
      },
      {values: true}
    );

    return () => unsubscribe();
  }, [form, speakerSocials]);

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
      {Object.entries(speakerSocials).map(([name, properties]) => (
        <div styleName="row" key={name}>
          <FinalInput
            name={`socials.${name}.url`}
            label={
              <p>
                {name} {properties.icon && <Icon name={properties.icon as SemanticICONS} />}
              </p>
            }
            initialValue={speaker.speaker_socials?.[name]?.url ?? ''}
          />
          <Popup
            content={Translate.string('Remove social')}
            position="right center"
            trigger={
              <Icon
                name="trash"
                link
                color="black"
                onClick={() => {
                  form.change(`socials.${name}`, undefined);
                  setSpeakerSocials(old =>
                    Object.fromEntries(Object.entries(old).filter(entry => entry[0] !== name))
                  );
                }}
              />
            }
          />
        </div>
      ))}
      <div styleName="centered-field">
        <Dropdown
          text={Translate.string('Add socials')}
          icon="add"
          floating
          labeled
          button
          className="icon"
        >
          <Dropdown.Menu>
            {DEFAULT_SOCIAL_TITLES.filter(entry => !speaker.speaker_socials?.[entry[0]]).map(
              name => (
                <Dropdown.Item
                  key={name}
                  icon={DEFAULT_SOCIAL_ICONS[name]}
                  text={name}
                  onClick={() => addSpeakerSocial(name, DEFAULT_SOCIAL_ICONS[name])}
                />
              )
            )}
            <Dropdown.Item text={Translate.string('Custom...')} onClick={openCustomSocialModal} />
          </Dropdown.Menu>
        </Dropdown>
      </div>
      {customSocialModalOpened && (
        <FinalModalForm
          id="add-social-form"
          onClose={closeCustomSocialModal}
          onSubmit={addSocial}
          header={Translate.string('Add Social')}
          size="tiny"
        >
          <FinalInput name="title" required fluid label={Translate.string('Title')} />
          <FinalDropdown
            name="icon"
            required
            label={Translate.string('Icon')}
            placeholder={Translate.string('Select Icon')}
            labeled
            fluid
            search
            selection
            options={ICON_OPTIONS}
          />
        </FinalModalForm>
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
      size="large"
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
