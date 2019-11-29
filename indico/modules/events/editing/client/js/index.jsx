// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:event_editing.api_file_types';

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import {camelizeKeys} from 'indico/utils/case';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import storeFactory from './store';
import Timeline from './components/Timeline';

document.addEventListener('DOMContentLoaded', async () => {
  const timelineElement = document.querySelector('#editing-timeline');
  const eventId = timelineElement.dataset.eventId;
  const downloadURL = timelineElement.dataset.downloadUrl;

  let response;
  try {
    response = await indicoAxios.get(fileTypesURL({confId: eventId}));
  } catch (e) {
    handleAxiosError(e);
  }
  const fileTypes = camelizeKeys(response.data);

  const store = storeFactory({
    eventId: parseInt(timelineElement.dataset.eventId, 10),
    contributionId: parseInt(timelineElement.dataset.contributionId, 10),
    editableType: timelineElement.dataset.editableType,
    downloadURL,
    fileTypes,
  });

  ReactDOM.render(
    <Provider store={store}>
      <Timeline />
    </Provider>,
    timelineElement
  );
});
