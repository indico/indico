// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import TagManager from './components/TagManager';

document.addEventListener('DOMContentLoaded', () => {
  const rootElement = document.querySelector('#editing-tags');
  if (!rootElement) {
    return;
  }

  const eventId = parseInt(rootElement.dataset.eventId, 10);
  ReactDOM.render(<TagManager eventId={eventId} />, rootElement);
});
