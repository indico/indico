// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import fileTypesURL from 'indico-url:event_editing.api_file_types';

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {camelizeKeys} from 'indico/utils/case';
import createReduxStore from 'indico/utils/redux';

import ReviewConditionsManager from './components/ReviewConditionsManager';

document.addEventListener('DOMContentLoaded', async () => {
  const reviewConditionsManager = document.querySelector('#editing-review-conditions');
  if (!reviewConditionsManager) {
    return null;
  }

  const eventId = parseInt(reviewConditionsManager.dataset.eventId, 10);
  const editableType = reviewConditionsManager.dataset.editableType;
  let fileTypes;

  try {
    const {data} = await indicoAxios.get(fileTypesURL({confId: eventId, type: editableType}));
    fileTypes = camelizeKeys(data);
  } catch (e) {
    handleAxiosError(e);
    return;
  }

  const store = createReduxStore(
    'editing-review-conditions',
    {},
    {
      staticData: {
        eventId,
        fileTypes,
      },
    }
  );

  ReactDOM.render(
    <Provider store={store}>
      <ReviewConditionsManager eventId={eventId} fileTypes={fileTypes} />
    </Provider>,
    reviewConditionsManager
  );
});
