// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import EditableType from './components/EditableType';

document.addEventListener('DOMContentLoaded', async () => {
  const editableType = document.querySelector('#editable-type');
  if (!editableType) {
    return;
  }
  const eventId = parseInt(editableType.dataset.eventId, 10);
  const type = editableType.dataset.editableType;
  ReactDOM.render(<EditableType eventId={eventId} editableType={type} />, editableType);
});
