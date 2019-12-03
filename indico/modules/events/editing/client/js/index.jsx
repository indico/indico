// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:event_editing.api_file_types';
import editableDetailsURL from 'indico-url:event_editing.api_editable';

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import {camelizeKeys} from 'indico/utils/case';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import storeFactory from './store';
import Timeline from './components/Timeline';

document.addEventListener('DOMContentLoaded', async () => {
  const timelineElement = document.querySelector('#editing-timeline');
  const eventId = parseInt(timelineElement.dataset.eventId, 10);

  let response;
  try {
    response = await indicoAxios.get(fileTypesURL({confId: eventId}));
  } catch (e) {
    handleAxiosError(e);
  }

  const fileTypes = camelizeKeys(response.data);
  const contributionId = parseInt(timelineElement.dataset.contributionId, 10);
  const editableType = timelineElement.dataset.editableType;
  const store = storeFactory({
    eventId,
    contributionId,
    editableType,
    fileTypes,
    editableDetailsURL: editableDetailsURL({
      confId: eventId,
      contrib_id: contributionId,
      type: editableType,
    }),
  });

  ReactDOM.render(
    <Provider store={store}>
      <Timeline />
    </Provider>,
    timelineElement
  );
});
