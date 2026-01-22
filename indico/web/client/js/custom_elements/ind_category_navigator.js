// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import CustomElementBase from 'indico/custom_elements/_base';
import CategoryNavigator from 'indico/react/components/category_navigator/CategoryNavigator';

console.log('[ind-category-navigator] Module loaded, registering custom element');
console.log('[ind-category-navigator] Document ready state:', document.readyState);
console.log(
  '[ind-category-navigator] Elements in DOM before registration:',
  document.querySelectorAll('ind-category-navigator').length
);

CustomElementBase.defineWhenDomReady(
  'ind-category-navigator',
  class extends CustomElementBase {
    constructor() {
      super();
      console.log('[ind-category-navigator] Constructor called');
    }

    connectedCallback() {
      console.log('[ind-category-navigator] connectedCallback called');
      super.connectedCallback();
    }

    setup() {
      console.log('[ind-category-navigator] Custom element setup called');
      ReactDOM.render(<CategoryNavigator />, this);
      console.log('[ind-category-navigator] CategoryNavigator React component rendered');
    }
  }
);

// Log when definition is complete
setTimeout(() => {
  console.log(
    '[ind-category-navigator] Custom element defined:',
    customElements.get('ind-category-navigator')
  );
  console.log(
    '[ind-category-navigator] Elements in DOM after registration:',
    document.querySelectorAll('ind-category-navigator')
  );
}, 100);
