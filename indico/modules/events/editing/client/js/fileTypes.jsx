// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import FileTypeManager from './components/FileTypeManager';

document.addEventListener('DOMContentLoaded', async () => {
  const fileTypeManager = document.querySelector('#editing-filetypes');
  if (!fileTypeManager) {
    return null;
  }
  const eventId = parseInt(fileTypeManager.dataset.eventId, 10);
  ReactDOM.render(<FileTypeManager eventId={eventId} />, fileTypeManager);
});
