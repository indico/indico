// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import createReduxStore from 'indico/utils/redux';

import {
  fetchLogEntries,
  setMetadataQuery,
  setInitialRealms,
  setHasNewEntries,
  setKeyword,
  setFilter,
} from './actions';
import EventLog from './components/EventLog';
import reducer from './reducers';

import '../style/logs.scss';

window.addEventListener('load', () => {
  const rootElement = document.querySelector('.event-log');
  const user = rootElement.dataset.user;
  const initialData = {
    staticData: {
      fetchLogsUrl: rootElement.dataset.fetchLogsUrl,
      realms: JSON.parse(rootElement.dataset.realms),
      pageSize: 15,
      user: user ? parseInt(user, 10) : null,
    },
  };
  const store = createReduxStore(
    'event-logs',
    {
      logs: reducer,
    },
    initialData
  );
  window.addEventListener('indico:logsRefresh', () => store.dispatch(setHasNewEntries()));

  // Set initial filters
  const initialFilters = JSON.parse(rootElement.dataset.initialFilters || '[]');
  const allRealms = Object.keys(initialData.staticData.realms);
  if (initialFilters.length > 0) {
    // Use filters from URL
    const filterState = Object.fromEntries(allRealms.map(r => [r, initialFilters.includes(r)]));
    store.dispatch(setFilter(filterState));
  } else {
    // Default: enable all realms
    store.dispatch(setInitialRealms(allRealms));
  }

  store.dispatch(setMetadataQuery(JSON.parse(rootElement.dataset.metadataQuery)));

  const initialKeyword = rootElement.dataset.initialKeyword;
  if (initialKeyword) {
    store.dispatch(setKeyword(initialKeyword));
  }

  ReactDOM.render(
    <Provider store={store}>
      <EventLog />
    </Provider>,
    rootElement
  );

  store.dispatch(fetchLogEntries());
});
