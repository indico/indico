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
import FileManager from './components/FileManager';
import Timeline from './components/Timeline';
import FileDisplay from './components/FileDisplay';

document.addEventListener('DOMContentLoaded', async () => {
  const fileManager = document.querySelector('#file-manager');
  const fileDisplay = document.querySelector('#file-display');
  const eventId = fileManager.dataset.eventId;

  let response;
  try {
    response = await indicoAxios.get(fileTypesURL({confId: eventId}));
  } catch (e) {
    handleAxiosError(e);
  }

  const fileTypes = camelizeKeys(response.data);
  try {
    response = await indicoAxios.get(fileManager.dataset.apiEditableUrl);
  } catch (e) {
    handleAxiosError(e);
  }

  const files = camelizeKeys(response.data.revisions[0].files);
  ReactDOM.render(
    <FileManager
      fileTypes={fileTypes}
      files={files}
      uploadURL={fileManager.dataset.uploadUrl}
      onChange={v => console.log(v)}
    />,
    fileManager
  );
  ReactDOM.render(
    <FileDisplay
      downloadURL={fileManager.dataset.downloadUrl}
      fileTypes={fileTypes}
      files={files}
    />,
    fileDisplay
  );

  const timelineRootElem = document.getElementById('editing-timeline');
  const store = storeFactory({
    eventId: parseInt(timelineRootElem.dataset.eventId, 10),
    contributionId: parseInt(timelineRootElem.dataset.contributionId, 10),
    editableType: timelineRootElem.dataset.editableType,
    fileTypes,
  });

  ReactDOM.render(
    <Provider store={store}>
      <Timeline />
    </Provider>,
    timelineRootElem
  );
});
