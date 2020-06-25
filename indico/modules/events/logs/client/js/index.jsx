// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import createReduxStore from 'indico/utils/redux';

import EventLog from './components/EventLog';
import {fetchLogEntries, setMetadataQuery} from './actions';
import reducer from './reducers';

import '../style/logs.scss';

window.addEventListener('load', () => {
  const rootElement = document.querySelector('.event-log');
  const initialData = {
    staticData: {
      fetchLogsUrl: rootElement.dataset.fetchLogsUrl,
      realms: JSON.parse(rootElement.dataset.realms),
      pageSize: 15,
    },
  };
  const store = createReduxStore(
    'event-logs',
    {
      logs: reducer,
    },
    initialData
  );
  store.dispatch(setMetadataQuery(JSON.parse(rootElement.dataset.metadataQuery)));

  ReactDOM.render(
    <Provider store={store}>
      <EventLog />
    </Provider>,
    rootElement
  );

  store.dispatch(fetchLogEntries());
});
