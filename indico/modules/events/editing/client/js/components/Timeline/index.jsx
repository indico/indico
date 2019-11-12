// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.
import editableDetailsURL from 'indico-url:event_editing.api_editable';

import React, {useEffect, useReducer} from 'react';
import PropTypes from 'prop-types';
import {Loader} from 'semantic-ui-react';

import TimelineHeader from 'indico/modules/events/reviewing/components/TimelineHeader';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';

import reducer from './reducer';
import * as actions from './actions';

export default function Timeline({eventId, editableId}) {
  const [{details, isLoading}, dispatch] = useReducer(reducer, {
    details: null,
    isLoading: false,
  });

  useEffect(() => {
    (async () => {
      dispatch(actions.setLoading(true));
      try {
        const {data} = await indicoAxios.get(
          editableDetailsURL({confId: eventId, editable_id: editableId})
        );
        dispatch(actions.setDetails(camelizeKeys(data)));
      } catch (error) {
        handleAxiosError(error, false, true);
      } finally {
        dispatch(actions.setLoading(false));
      }
    })();
  }, [editableId, eventId]);

  if (isLoading) {
    return <Loader active />;
  } else if (!details) {
    return null;
  }

  const {contribution, revisions} = details;

  const lastRevision = revisions[revisions.length - 1];
  const state =
    lastRevision.finalState.name === 'none' ? lastRevision.initialState : lastRevision.finalState;

  return (
    <TimelineHeader
      contribution={contribution}
      state={state}
      submitter={revisions[0].submitter}
      eventId={eventId}
    >
      STUFF
    </TimelineHeader>
  );
}

Timeline.propTypes = {
  eventId: PropTypes.string.isRequired,
  editableId: PropTypes.string.isRequired,
};
