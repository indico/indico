// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import EditingManagement from './EditingManagement';

document.addEventListener('DOMContentLoaded', async () => {
  const editingManagementContainer = document.querySelector('#editing-management');
  if (!editingManagementContainer) {
    return;
  }
  ReactDOM.render(<EditingManagement />, editingManagementContainer);
});
