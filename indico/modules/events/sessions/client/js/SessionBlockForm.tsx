// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import locationParentURL from 'indico-url:sessions.api_blocks_location_parent';
import sessionBlockCreateURL from 'indico-url:sessions.api_create_session_block';
import sessionBlockURL from 'indico-url:sessions.api_manage_block';

import _ from 'lodash';
import React, {useState, useEffect} from 'react';
import {Button, Dimmer, Loader} from 'semantic-ui-react';

import {LocationParentObj} from 'indico/modules/events/timetable/types';
import {FinalLocationField} from 'indico/react/components';
import {FinalSessionBlockPersonLinkField} from 'indico/react/components/PersonLinkField';
import {FinalInput} from 'indico/react/forms';
import {FinalDateTimePicker, FinalDuration} from 'indico/react/forms/fields';
import {FinalModalForm, handleSubmitError} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

interface SessionBlockEditFormProps {
  eventId: number;
  sessionId: number;
  blockId: number;
  onClose: () => void;
}

interface SessionBlockFormFieldProps {
  eventId: number;
  locationParent: LocationParentObj;
  extraOptions?: Record<string, any>;
  [key: string]: any; // Allow additional props
}

export function SessionBlockFormFields({
  eventId,
  locationParent,
  extraOptions = {},
}: SessionBlockFormFieldProps) {
  const {minStartDt, maxEndDt} = extraOptions;

  return (
    <>
      <FinalInput
        name="title"
        label={Translate.string('Title')}
        description={Translate.string('Title of the session block')}
        autoFocus
      />
      <FinalDateTimePicker
        name="start_dt"
        label={Translate.string('Start time')}
        required
        minStartDt={minStartDt}
        maxEndDt={maxEndDt}
      />
      <FinalDuration name="duration" label={Translate.string('Duration')} required />
      <FinalSessionBlockPersonLinkField
        name="person_links"
        label={Translate.string('Conveners')}
        eventId={eventId}
        sessionUser={{...Indico.User, userId: Indico.User.id}}
      />
      <FinalLocationField
        name="location_data"
        label={Translate.string('Location')}
        locationParent={locationParent}
      />
      <FinalInput name="code" label={Translate.string('Program code')} />
    </>
  );
}

export default function SessionBlockEditForm({
  eventId,
  sessionId,
  blockId,
  onClose,
}: SessionBlockEditFormProps) {
  const {data: blockData, loading} = useIndicoAxios(
    sessionBlockURL({event_id: eventId, session_id: sessionId, block_id: blockId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId, session_id: sessionId})
  );

  const handleSubmit = async (formData: any) => {
    const personLinks = formData.conveners.map(
      ({
        affiliationMeta,
        affiliationId,
        type,
        avatarURL,
        favoriteUsers,
        fullName,
        id,
        isAdmin,
        language,
        name,
        userId,
        userIdentifier,
        invalid,
        detail,
        ...rest
      }: any) => ({
        ...rest,
      })
    );
    formData = {
      ...formData,
      conveners: snakifyKeys(personLinks),
    };
    try {
      await indicoAxios.patch(
        sessionBlockURL({event_id: eventId, session_id: sessionId, block_id: blockId}),
        formData
      );
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    await new Promise(() => {});
  };

  if (loading || locationParentLoading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  return (
    <FinalModalForm
      id="session-block-form"
      header={Translate.string("Edit session block '{session_block_title}'", {
        session_block_title: blockData.title,
      })}
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={{...blockData, conveners: camelizeKeys(blockData.conveners)}}
      size="small"
    >
      <SessionBlockFormFields eventId={eventId} locationParent={locationParent} />
    </FinalModalForm>
  );
}

interface SessionBlockCreateFormProps {
  eventId: number;
  sessionId: number;
  onClose: () => void;
}

export function SessionBlockCreateForm({eventId, sessionId, onClose}: SessionBlockCreateFormProps) {
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId, session_id: sessionId})
  );

  const handleSubmit = async (formData: any) => {
    formData = _.omitBy(formData, 'person_links'); // TODO person links
    try {
      await indicoAxios.patch(
        sessionBlockCreateURL({event_id: eventId, session_id: sessionId}),
        formData
      );
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    // eslint-disable-next-line @typescript-eslint/no-empty-function
    await new Promise(() => {});
  };

  if (locationParentLoading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  const locationData = locationParent
    ? {...locationParent.location_data, inheriting: true}
    : {inheriting: false};

  return (
    <FinalModalForm
      id="session-block-form"
      header={Translate.string('Add new session block')}
      onSubmit={handleSubmit}
      onClose={onClose}
      initialValues={{location_data: locationData}}
      size="small"
    >
      <SessionBlockFormFields eventId={eventId} locationParent={locationParent} />
    </FinalModalForm>
  );
}

interface EditSessionBlockButtonProps {
  eventId: number;
  sessionId: number;
  blockId: number;
  eventTitle: string;
  eventType: string;
  triggerSelector?: string;
}

export function EditSessionBlockButton({
  eventId,
  sessionId,
  blockId,
  eventTitle,
  eventType,
  triggerSelector,
  ...rest
}: EditSessionBlockButtonProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!triggerSelector) {
      return;
    }
    const handler = () => setOpen(true);
    const element = document.querySelector(triggerSelector);
    element.addEventListener('click', handler);
    return () => element.removeEventListener('click', handler);
  }, [triggerSelector]);

  return (
    <>
      {!triggerSelector && (
        <Button onClick={() => setOpen(true)} {...rest}>
          <Translate>Edit contribution</Translate>
        </Button>
      )}
      {open && (
        <SessionBlockEditForm
          eventId={eventId}
          sessionId={sessionId}
          blockId={blockId}
          eventType={eventType}
          eventTitle={eventTitle}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}

interface EditSessionBlockCreateButtonProps {
  eventId: number;
  sessionId: number;
  eventTitle: string;
  eventType: string;
  triggerSelector?: string;
}

export function EditSessionBlockCreateButton({
  eventId,
  sessionId,
  eventTitle,
  eventType,
  triggerSelector,
  ...rest
}: EditSessionBlockCreateButtonProps) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!triggerSelector) {
      return;
    }
    const handler = () => setOpen(true);
    const element = document.querySelector(triggerSelector);
    element.addEventListener('click', handler);
    return () => element.removeEventListener('click', handler);
  }, [triggerSelector]);

  return (
    <>
      {!triggerSelector && (
        <Button onClick={() => setOpen(true)} {...rest}>
          <Translate>Edit contribution</Translate>
        </Button>
      )}
      {open && (
        <SessionBlockEditForm
          eventId={eventId}
          sessionId={sessionId}
          eventType={eventType}
          eventTitle={eventTitle}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}
