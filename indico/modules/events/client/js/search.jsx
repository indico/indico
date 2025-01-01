// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import eventSearchURL from 'indico-url:search.event_search';

import React from 'react';
import ReactDOM from 'react-dom';

import SearchBox from 'indico/modules/search/components/SearchBox';

document.addEventListener('DOMContentLoaded', () => {
  const domContainer = document.querySelector('#event-search-box');

  if (domContainer) {
    const eventId = parseInt(domContainer.dataset.eventId, 10);
    const isAdmin = domContainer.dataset.isAdmin !== undefined;

    ReactDOM.render(
      <SearchBox
        onSearch={(keyword, __, adminOverrideEnabled) => {
          const params = {q: keyword, event_id: eventId};
          if (isAdmin && adminOverrideEnabled) {
            params.admin_override_enabled = true;
          }
          window.location = eventSearchURL(params);
        }}
        isAdmin={isAdmin}
      />,
      domContainer
    );
  }
});
