// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import locationParentURL from 'indico-url:sessions.api_blocks_location_parent';
import sessionBlockCreateURL from 'indico-url:sessions.api_create_block';
import sessionBlockURL from 'indico-url:sessions.api_manage_block';

import _ from 'lodash';
import PropTypes from 'prop-types';
import React, {useState, useEffect} from 'react';
import {Button, Dimmer, Loader} from 'semantic-ui-react';

import {FinalLocationField} from 'indico/react/components';
import {FinalSessionBlockPersonLinkField} from 'indico/react/components/PersonLinkField';
import {FinalInput} from 'indico/react/forms';
import {FinalDuration, FinalTimePicker} from 'indico/react/forms/fields';
import {FinalModalForm, handleSubmitError} from 'indico/react/forms/final-form';
import {useIndicoAxios} from 'indico/react/hooks';
import {Translate} from 'indico/react/i18n';
import {indicoAxios} from 'indico/utils/axios';
import {camelizeKeys, snakifyKeys} from 'indico/utils/case';

export default function SessionBlockEditForm({eventId, sessionId, blockId, onClose}) {
  const {data: blockData, loading} = useIndicoAxios(
    sessionBlockURL({event_id: eventId, session_id: sessionId, block_id: blockId})
  );
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId, session_id: sessionId})
  );

  const handleSubmit = async formData => {
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
      }) => ({
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
      <FinalInput
        name="title"
        label={Translate.string('Title')}
        description={Translate.string('Title of the session block')}
        autoFocus
        required
      />
      <FinalTimePicker name="start_dt" label={Translate.string('Start time')} required />
      <FinalDuration name="duration" label={Translate.string('Duration')} required />
      <FinalSessionBlockPersonLinkField
        name="conveners"
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
    </FinalModalForm>
  );
}

SessionBlockEditForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  sessionId: PropTypes.number.isRequired,
  blockId: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
};

function SessionBlockCreateForm({eventId, sessionId, onClose}) {
  const {data: locationParent, loading: locationParentLoading} = useIndicoAxios(
    locationParentURL({event_id: eventId, session_id: sessionId})
  );

  const handleSubmit = async formData => {
    formData = _.omitBy(formData, 'conveners'); // TODO person links
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
      <FinalInput
        name="title"
        label={Translate.string('Title')}
        description={Translate.string('Title of the session block')}
        autoFocus
        required
      />
      <FinalTimePicker name="start_dt" label={Translate.string('Start time')} required />
      <FinalDuration name="duration" label={Translate.string('Duration')} required />
      <FinalSessionBlockPersonLinkField
        name="conveners"
        label={Translate.string('Conveners')}
        eventId={eventId}
        sessionUser={Indico.User}
      />
      <FinalLocationField
        name="location_data"
        label={Translate.string('Location')}
        locationParent={locationParent}
      />
      <FinalInput name="code" label={Translate.string('Program code')} />
    </FinalModalForm>
  );
}

SessionBlockCreateForm.propTypes = {
  eventId: PropTypes.number.isRequired,
  sessionId: PropTypes.number.isRequired,
  onClose: PropTypes.func.isRequired,
};

export function EditSessionBlockButton({
  eventId,
  sessionId,
  blockId,
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

EditSessionBlockButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  sessionId: PropTypes.number.isRequired,
  blockId: PropTypes.number.isRequired,
  eventType: PropTypes.string.isRequired,
  eventTitle: PropTypes.string.isRequired,
  triggerSelector: PropTypes.string,
};

EditSessionBlockButton.defaultProps = {
  triggerSelector: null,
};

export function EditSessionBlockCreateButton({
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

EditSessionBlockCreateButton.propTypes = {
  eventId: PropTypes.number.isRequired,
  sessionId: PropTypes.number.isRequired,
  blockId: PropTypes.number.isRequired,
  eventType: PropTypes.string.isRequired,
  eventTitle: PropTypes.string.isRequired,
  triggerSelector: PropTypes.string,
};

EditSessionBlockCreateButton.defaultProps = {
  triggerSelector: null,
};
