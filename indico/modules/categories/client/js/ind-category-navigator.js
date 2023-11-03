// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import * as categoryNavigator from 'indico/react/components/category_navigator';

import NavigateTo from './components/NavigateTo';

customElements.define(
  'ind-category-navigator',
  class extends HTMLElement {
    connectedCallback() {
      const options = {
        trigger: document.getElementById(this.getAttribute('triggeredby')),
        categoryId: this.getAttribute('category-id'),
      };
      ReactDOM.render(
        <categoryNavigator.DialogViewModel
          view={categoryNavigator.DialogView}
          actionView={NavigateTo}
          {...options}
        />,
        this
      );
    }
  }
);
