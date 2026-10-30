// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import locationParentURL from 'indico-url:sessions.api_blocks_location_parent';
import sessionBlockURL from 'indico-url:sessions.api_manage_block';

import {FormApi} from 'final-form';
import React, {useState} from 'react';
import {Field} from 'react-final-form';
import {Dimmer, Loader} from 'semantic-ui-react';

import {LocationParentObj} from 'indico/modules/events/timetable/types';
import {FinalLocationField, FinalSessionBlockPersonLinkField} from 'indico/react/components';
import {FinalInput} from 'indico/react/forms';
import {FinalDateTimePicker, FinalDuration} from 'indico/react/forms/fields';
import {FinalModalForm, getChangedValues, handleSubmitError} from 'indico/react/forms/final-form';
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
      <Field name="duration" subscription={{value: true}}>
        {({input: {value: duration}}) => (
          <FinalDateTimePicker
            name="start_dt"
            label={Translate.string('Start time')}
            required
            minStartDt={minStartDt}
            maxEndDt={maxEndDt ? maxEndDt.clone().subtract(duration, 'seconds') : null}
          />
        )}
      </Field>
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

function SessionBlockEditForm({eventId, sessionId, blockId, onClose}: SessionBlockEditFormProps) {
  const {data: blockData, loading} = useIndicoAxios(
    sessionBlockURL({event_id: eventId, session_id: sessionId, block_id: blockId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId, session_id: sessionId})
  );

  const handleSubmit = async (formData: any, form: FormApi) => {
    const personLinks = formData.person_links.map(
      ({
        affiliationMeta,
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
        ...personLinkData
      }: any) =>
        snakifyKeys({
          ...personLinkData,
        })
    );
    formData = {
      ...formData,
      person_links: personLinks,
    };
    const changedValues = getChangedValues(formData, form);
    try {
      await indicoAxios.patch(
        sessionBlockURL({event_id: eventId, session_id: sessionId, block_id: blockId}),
        changedValues
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
      initialValues={{
        ...blockData,
        person_links: camelizeKeys(blockData.person_links),
      }}
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
}

export function EditSessionBlockButton({eventId, sessionId, blockId}: EditSessionBlockButtonProps) {
  const [open, setOpen] = useState(false);

  return (
    <>
      <a
        className="i-link highlight icon-edit js-hide-balloon"
        title={Translate.string('Edit session block (new React-based dialog)')}
        onClick={() => {
          setOpen(true);
        }}
      />
      {open && (
        <SessionBlockEditForm
          eventId={eventId}
          sessionId={sessionId}
          blockId={blockId}
          onClose={() => setOpen(false)}
        />
      )}
    </>
  );
}
