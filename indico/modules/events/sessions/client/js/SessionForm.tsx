// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createSessionURL from 'indico-url:sessions.api_create_session';
import sessionURL from 'indico-url:sessions.api_manage_session';
import sessionColorURL from 'indico-url:sessions.api_random_session_color';
import locationParentURL from 'indico-url:sessions.api_sessions_location_parent';
import typesURL from 'indico-url:sessions.types_rest';

import {FormApi} from 'final-form';
import React, {useState} from 'react';
import {Dimmer, Loader} from 'semantic-ui-react';

import {FinalLocationField, FinalSessionColorPicker} from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDropdown, FinalDuration} from 'indico/react/forms/fields';
import {FinalModalForm, getChangedValues, handleSubmitError} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

interface SessionFormProps {
  eventType: string;
  sessionTypes: {key: number; text: string; value: number}[];
  initialValues: any;
  header: string;
  locationParent: any;
  onSubmit: (formData: any, form?: any) => void;
  onClose: () => void;
}

interface SessionFormFieldsProps {
  eventType: string;
  sessionTypes: {key: number; text: string; value: number}[];
  locationParent: any;
}

export function SessionFormFields({
  eventType,
  sessionTypes,
  locationParent,
}: SessionFormFieldsProps) {
  return (
    <>
      <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
      <FinalTextArea name="description" label={Translate.string('Description')} />
      {eventType === 'conference' && sessionTypes.length > 0 && (
        <FinalDropdown
          name="type"
          label={Translate.string('Session type')}
          placeholder={Translate.string('No type selected')}
          options={sessionTypes}
          selection
          nullIfEmpty
        />
      )}
      {eventType === 'conference' && (
        <FinalInput
          name="code"
          label={Translate.string('Session code')}
          description={Translate.string(
            'The code that will identify the session in the Book of Abstracts.'
          )}
        />
      )}
      <FinalDuration
        name="default_contribution_duration"
        label={Translate.string('Default contribution duration')}
        description={Translate.string(
          'Duration that a contribution created within this session will have by default.'
        )}
        required
      />
      <FinalSessionColorPicker name="colors" label={Translate.string('Color')} />
      <FinalLocationField
        name="location_data"
        label={Translate.string('Default location')}
        description={Translate.string('Default location for blocks inside the session.')}
        locationParent={locationParent}
      />
    </>
  );
}

export function SessionForm({
  eventType,
  sessionTypes,
  initialValues,
  header,
  locationParent,
  onSubmit,
  onClose,
}: SessionFormProps) {
  return (
    <FinalModalForm
      id="session-form"
      style={{overflowWrap: 'break-word'}}
      header={header}
      onSubmit={onSubmit}
      onClose={onClose}
      initialValues={initialValues}
      size="small"
    >
      <SessionFormFields {...{eventType, sessionTypes, locationParent}} />
    </FinalModalForm>
  );
}

interface SessionEditFormProps {
  eventId: number;
  sessionId: number;
  eventType: string;
  onClose: () => void;
}

export default function SessionEditForm({
  eventId,
  sessionId,
  eventType,
  onClose,
}: SessionEditFormProps) {
  const {data: sessionTypesData, loading: typesLoading} = useIndicoAxios(
    typesURL({event_id: eventId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId})
  );
  const {data: sessionData, loading} = useIndicoAxios(
    sessionURL({event_id: eventId, session_id: sessionId})
  );

  const handleSubmit = async (formData: any, form: FormApi) => {
    const submitPayload = getChangedValues(formData, form);
    try {
      await indicoAxios.patch(
        sessionURL({event_id: eventId, session_id: sessionId}),
        submitPayload
      );
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    await new Promise(() => {});
  };

  if (loading || typesLoading || locationParentLoading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  const sessionTypes = sessionTypesData.map(({id, name}: {id: number; name: string}) => ({
    key: id,
    text: name,
    value: id,
  }));

  return (
    <SessionForm
      eventType={eventType}
      initialValues={sessionData}
      sessionTypes={sessionTypes}
      onSubmit={handleSubmit}
      onClose={onClose}
      header={Translate.string("Edit session '{session_title}'", {
        session_title: sessionData.title,
      })}
      locationParent={locationParent}
    />
  );
}

interface SessionCreateFormProps {
  eventId: number;
  eventType: string;
  onClose: () => void;
}

export function SessionCreateForm({eventId, eventType, onClose}: SessionCreateFormProps) {
  const {data: sessionTypesData, loading: typesLoading} = useIndicoAxios(
    typesURL({event_id: eventId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId})
  );
  const {data: sessionColor, loading: sessionColorLoading} = useIndicoAxios(
    sessionColorURL({event_id: eventId})
  );

  const handleSubmit = async (formData: any) => {
    if (formData.type === '') {
      formData.type = null;
    }
    try {
      await indicoAxios.post(createSessionURL({event_id: eventId}), formData);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    await new Promise(() => {});
  };

  if (typesLoading || locationParentLoading || sessionColorLoading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  const sessionTypes = sessionTypesData.map(({id, name}: {id: number; name: string}) => ({
    key: id,
    text: name,
    value: id,
  }));

  const locationData = locationParent
    ? {...locationParent.location_data, inheriting: true}
    : {inheriting: false};

  return (
    <SessionForm
      eventType={eventType}
      initialValues={{colors: sessionColor, location_data: locationData}}
      sessionTypes={sessionTypes}
      onSubmit={handleSubmit}
      onClose={onClose}
      header={Translate.string('Add new session')}
      locationParent={locationParent}
    />
  );
}

interface EditSessionButtonProps {
  eventId: number;
  sessionId: number;
  eventType: string;
}

export function EditSessionButton({eventId, sessionId, eventType}: EditSessionButtonProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <a
        className="i-link highlight icon-edit hide-if-locked"
        title={Translate.string('Edit this session (new React-based dialog)')}
        onClick={evt => {
          evt.preventDefault();
          evt.stopPropagation();
          setOpen(true);
        }}
      />
      {open && (
        <SessionEditForm
          eventId={eventId}
          sessionId={sessionId}
          eventType={eventType}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

interface CreateSessionButtonProps {
  eventId: number;
  eventType: string;
}

export function CreateSessionButton({eventId, eventType}: CreateSessionButtonProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button type="button" className="i-button highlight icon-plus" onClick={() => setOpen(true)}>
        <Translate>Add new session (React)</Translate>
      </button>
      {open && (
        <SessionCreateForm eventId={eventId} eventType={eventType} onClose={() => setOpen(false)} />
      )}
    </>
  );
}
