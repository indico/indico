// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import EditableTypeList from './components/EditableTypeList';

document.addEventListener('DOMContentLoaded', async () => {
  const editableTypeList = document.querySelector('#editable-type-list');
  if (!editableTypeList) {
    return null;
  }
  const eventId = parseInt(editableTypeList.dataset.eventId, 10);
  ReactDOM.render(<EditableTypeList eventId={eventId} />, editableTypeList);
});
