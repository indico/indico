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
      ReactDOM.render(
        <categoryNavigator.DialogViewModel
          categoryId={this.categoryId}
          view={categoryNavigator.DialogView}
        />,
        this
      );
      this.trigger.addEventListener('click', this.navigate);
    }

    disconnectedCallback() {
      this.trigger.removeEventListener('click', this.navigate);
      ReactDOM.unmountComponentAtNode(this);
    }

    get categoryId() {
      return this.getAttribute('category-id');
    }

    get trigger() {
      return document.getElementById(this.getAttribute('triggeredby'));
    }

    navigate = () => {
      window.dispatchEvent(new CustomEvent('open-category-navigator', {detail: NavigateTo}));
    };
  }
);
