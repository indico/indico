// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import eventSearchUrl from 'indico-url:search.event_search';

import React from 'react';
import ReactDOM from 'react-dom';

import SearchBox from 'indico/modules/search/components/SearchBox';

document.addEventListener('DOMContentLoaded', () => {
  const domContainer = document.querySelector('#event-search-box');

  if (domContainer) {
    const eventId = parseInt(domContainer.dataset.eventId, 10);

    ReactDOM.render(
      <SearchBox
        onSearch={keyword => {
          window.location = eventSearchUrl({event_id: eventId, q: keyword});
        }}
      />,
      domContainer
    );
  }
});
