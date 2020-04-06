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
import createReduxStore from 'indico/utils/redux';

import EditingView from './page_layout';
import Timeline from './timeline';
import reducer from './timeline/reducer';

document.addEventListener('DOMContentLoaded', async () => {
  const editingElement = document.querySelector('#editing-view');

  if (!editingElement) {
    return;
  }

  const headerHeight =
    document.querySelector('div.header').getBoundingClientRect().height +
    document.querySelector('div.main-breadcrumb').getBoundingClientRect().height;
  document.body.style.setProperty('--header-height', headerHeight);

  const eventId = parseInt(editingElement.dataset.eventId, 10);
  const eventTitle = editingElement.dataset.eventTitle;
  const contributionId = parseInt(editingElement.dataset.contributionId, 10);
  const contributionCode = editingElement.dataset.contributionCode;
  const editableType = editingElement.dataset.editableType;

  let fileTypes, tags;

  try {
    const [fileTypeResponse, tagResponse] = await Promise.all([
      indicoAxios.get(fileTypesURL({confId: eventId, type: editableType})),
      indicoAxios.get(tagsURL({confId: eventId})),
    ]);
    fileTypes = camelizeKeys(fileTypeResponse.data);
    tags = camelizeKeys(tagResponse.data);
  } catch (e) {
    handleAxiosError(e);
    return;
  }

  const store = createReduxStore(
    'editing-timeline',
    {timeline: reducer},
    {
      staticData: {
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
      },
    }
  );

  ReactDOM.render(
    <Provider store={store}>
      <EditingView eventId={eventId} eventTitle={eventTitle}>
        <Timeline />
      </EditingView>
    </Provider>,
    editingElement
  );
});
