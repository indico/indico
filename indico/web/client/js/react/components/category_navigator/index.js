// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {injectModal} from 'indico/react/util';

import CategoryNavigator from './CategoryNavigator';

export default CategoryNavigator;

export function showCategoryNavigator(options = {}) {
  return injectModal(resolve => (
    <CategoryNavigator
      {...options}
      onClose={() => {
        if (options.onClose) {
          options.onClose();
        }
        resolve(null);
      }}
      onAction={async category => {
        let res;
        if (options.onAction) {
          res = options.onAction(category);
        }
        if (res && typeof res.then === 'function') {
          // A rejected action keeps the navigator open; the navigator handles the rejection
          await res;
        }
        resolve(category);
      }}
    />
  ));
}

export function renderInlineCategoryNavigator(element, options = {}) {
  ReactDOM.render(<CategoryNavigator {...options} inline />, element);
}

export function unmountInlineCategoryNavigator(element) {
  ReactDOM.unmountComponentAtNode(element);
}
