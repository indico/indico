// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import FieldsDemo from './FieldsDemo';

(function(global) {
  global.setupFields = function setupFields() {
    const root = document.querySelector('#fields-container');
    if (root) {
      ReactDOM.render(<FieldsDemo />, root);
    }
  };
})(window);
