// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
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
import EditingView from './components/EditingView';

document.addEventListener('DOMContentLoaded', async () => {
  const editingElement = document.querySelector('#editing-view');

  if (!editingElement) {
    return;
  }

  const eventId = parseInt(editingElement.dataset.eventId, 10);
  const eventTitle = editingElement.dataset.eventTitle;

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
    return;
  }

  const contributionId = parseInt(editingElement.dataset.contributionId, 10);
  const contributionCode = editingElement.dataset.contributionCode;
  const editableType = editingElement.dataset.editableType;
  const store = storeFactory({
    eventId,
    contributionId,
    contributionCode,
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
      <EditingView eventTitle={eventTitle} />
    </Provider>,
    editingElement
  );
});
