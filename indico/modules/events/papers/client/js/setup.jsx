// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import createReduxStore from 'indico/utils/redux';

import Paper from './components/Paper';
import paperReducers from './reducers';

export default () => {
  const rootElement = document.querySelector('.paper-timeline');
  if (!rootElement) {
    return;
  }

  const eventId = parseInt(rootElement.dataset.eventId, 10);
  const contributionId = parseInt(rootElement.dataset.contribId, 10);
  const initialData = {
    staticData: {
      user: {
        fullName: Indico.User.fullName,
        avatarURL: Indico.User.avatarURL,
      },
    },
  };
  const store = createReduxStore('paper-timeline', {paper: paperReducers}, initialData);

  ReactDOM.render(
    <Provider store={store}>
      <Paper eventId={eventId} contributionId={contributionId} />
    </Provider>,
    rootElement
  );
};
