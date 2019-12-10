// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:event_editing.api_file_types';
import editableDetailsURL from 'indico-url:event_editing.api_editable';
import tagsURL from 'indico-url:event_editing.api_tags';

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import {camelizeKeys} from 'indico/utils/case';
import {indicoAxios, handleAxiosError} from 'indico/utils/axios';

import storeFactory from './store';
import Timeline from './components/Timeline';

document.addEventListener('DOMContentLoaded', async () => {
  const timelineElement = document.querySelector('#editing-timeline');

  if (!timelineElement) {
    return;
  }

  const eventId = parseInt(timelineElement.dataset.eventId, 10);
  let fileTypes, tags;

  try {
    const [fileTypeResponse, tagResponse] = await Promise.all([
      indicoAxios.get(fileTypesURL({confId: eventId})),
      indicoAxios.get(tagsURL({confId: eventId})),
    ]);
    fileTypes = camelizeKeys(fileTypeResponse.data);
    tags = camelizeKeys(tagResponse.data);
  } catch (e) {
    handleAxiosError(e);
  }

  const contributionId = parseInt(timelineElement.dataset.contributionId, 10);
  const editableType = timelineElement.dataset.editableType;
  const store = storeFactory({
    eventId,
    contributionId,
    editableType,
    fileTypes,
    tags,
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
