// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import sessionURL from 'indico-url:sessions.api_manage_session';
import sessionColorURL from 'indico-url:sessions.api_random_session_color';
import locationParentURL from 'indico-url:sessions.api_sessions_location_parent';
import typesURL from 'indico-url:sessions.types_rest';

import {FormApi} from 'final-form';
import React from 'react';
import {useDispatch, useSelector} from 'react-redux/es';
import {Dimmer, Loader} from 'semantic-ui-react';

import {SessionForm} from 'indico/modules/events/sessions/SessionForm';
import {getChangedValues} from 'indico/react/forms';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';

import * as actions from './actions';
import * as selectors from './selectors';

interface TimetableSessionEditModalProps {
  sessionId: number;
  onClose: () => void;
}

export function TimetableSessionEditModal({sessionId, onClose}: TimetableSessionEditModalProps) {
  const dispatch = useDispatch<any>();
  const eventId = useSelector(selectors.getEventId);
  const eventType = useSelector(selectors.getEventType);

  const {data: sessionTypesData, loading: typesLoading} = useIndicoAxios(
    typesURL({event_id: eventId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId})
  );
  const {data: sessionData, loading} = useIndicoAxios(
    sessionURL({event_id: eventId, session_id: sessionId})
  );

  const handleSubmit = (formData: any, form: FormApi) => {
    dispatch(actions.editSession(formData.id, getChangedValues(formData, form)));
    onClose();
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

interface TimetableSessionCreateModalProps {
  onClose: () => void;
}

export function TimetableSessionCreateModal({onClose}: TimetableSessionCreateModalProps) {
  const dispatch = useDispatch<any>();
  const eventId = useSelector(selectors.getEventId);
  const eventType = useSelector(selectors.getEventType);

  const {data: sessionTypesData, loading: typesLoading} = useIndicoAxios(
    typesURL({event_id: eventId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId})
  );
  const {data: sessionColor, loading: sessionColorLoading} = useIndicoAxios(
    sessionColorURL({event_id: eventId})
  );

  const handleSubmit = (formData: any) => {
    dispatch(actions.createSession(formData));
    onClose();
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
