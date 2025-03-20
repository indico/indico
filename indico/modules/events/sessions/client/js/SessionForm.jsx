// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createSessionURL from 'indico-url:sessions.api_create_session';
import sessionURL from 'indico-url:sessions.api_manage_session';
import sessionColorURL from 'indico-url:sessions.api_random_session_color';
import locationParentURL from 'indico-url:sessions.api_sessions_location_parent';
import typesURL from 'indico-url:sessions.types_rest';

import PropTypes from 'prop-types';
import React, {useState, useEffect} from 'react';
import {Button, Dimmer, Loader} from 'semantic-ui-react';

import {FinalLocationField, FinalSessionColorPicker} from 'indico/react/components';
import {FinalInput, FinalTextArea} from 'indico/react/forms';
import {FinalDropdown, FinalDuration} from 'indico/react/forms/fields';
import {FinalModalForm, handleSubmitError} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';

function SessionForm({
  eventType,
  sessionTypes,
  initialValues,
  header,
  locationParent,
  onSubmit,
  onClose,
}) {
  return (
    <FinalModalForm
      id="session-form"
      header={header}
      onSubmit={onSubmit}
      onClose={onClose}
      initialValues={initialValues}
      size="small"
    >
      <FinalInput name="title" label={Translate.string('Title')} autoFocus required />
      <FinalTextArea name="description" label={Translate.string('Description')} />
      {eventType === 'conference' && sessionTypes.length > 0 && (
        <FinalDropdown
          name="type"
          label={Translate.string('Session type')}
          placeholder={Translate.string('No type selected')}
          options={sessionTypes}
          selection
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
    </FinalModalForm>
  );
}

SessionForm.propTypes = {
  eventType: PropTypes.string.isRequired,
  sessionTypes: PropTypes.array.isRequired,
  initialValues: PropTypes.object.isRequired,
  header: PropTypes.string.isRequired,
  locationParent: PropTypes.object,
  onSubmit: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};

SessionForm.defaultProps = {
  locationParent: null,
};

export default function SessionEditForm({eventId, sessionId, eventType, onClose}) {
  const {data: sessionTypesData, loading: typesLoading} = useIndicoAxios(
    typesURL({event_id: eventId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId})
  );
  const {data: sessionData, loading} = useIndicoAxios(
    sessionURL({event_id: eventId, session_id: sessionId})
  );

  const handleSubmit = async formData => {
    if (formData.type === '') {
      formData.type = null;
    }
    try {
      await indicoAxios.patch(sessionURL({event_id: eventId, session_id: sessionId}), formData);
    } catch (e) {
      return handleSubmitError(e);
    }
    location.reload();
    // never finish submitting to avoid fields being re-enabled
    await new Promise(() => {});
  };

  if (loading || typesLoading || locationParentLoading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  const sessionTypes = sessionTypesData.map(({id, name}) => ({
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

SessionEditForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  sessionId: PropTypes.number.isRequired,
  eventType: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export function SessionCreateForm({eventId, eventType, onClose}) {
  const {data: sessionTypesData, loading: typesLoading} = useIndicoAxios(
    typesURL({event_id: eventId})
  );
  // const {data: locationsData, loading: locationsLoading} = useIndicoAxios(locationsURL());
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId})
  );
  const {data: sessionColor, loading: sessionColorLoading} = useIndicoAxios(
    sessionColorURL({event_id: eventId})
  );

  // const {data, loading} = useIndicoAxios(sessionFormDataURL({event_id: eventId}));

  const handleSubmit = async formData => {
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
    await new Promise(() => {});
  };

  if (typesLoading || locationParentLoading || sessionColorLoading) {
    return (
      <Dimmer active>
        <Loader />
      </Dimmer>
    );
  }

  const sessionTypes = sessionTypesData.map(({id, name}) => ({
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

SessionCreateForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  eventType: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
};

export function EditSessionButton({
  eventId,
  sessionId,
  eventTitle,
  eventType,
  triggerSelector,
  ...rest
}) {
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
        <SessionEditForm
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

EditSessionButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  sessionId: PropTypes.number.isRequired,
  eventType: PropTypes.string.isRequired,
  eventTitle: PropTypes.string.isRequired,
  triggerSelector: PropTypes.string,
};

EditSessionButton.defaultProps = {
  triggerSelector: null,
};

export function AddSessionButton({eventId, eventType, triggerSelector, ...rest}) {
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
        <SessionCreateForm eventId={eventId} eventType={eventType} onClose={() => setOpen(false)} />
      )}
    </>
  );
}

AddSessionButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  eventType: PropTypes.string.isRequired,
  triggerSelector: PropTypes.string,
};

AddSessionButton.defaultProps = {
  triggerSelector: null,
};
