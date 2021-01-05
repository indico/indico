// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import './display';
import {setMomentLocale} from 'indico/utils/date';
import CategoryStatistics from './components/CategoryStatistics';
import {LocaleContext} from './context.js';

(function(global) {
  global.setupCategoryStats = function setupCategoryStats() {
    document.addEventListener('DOMContentLoaded', async () => {
      const rootElement = document.querySelector('#category-stats-root');
      if (!rootElement) {
        return;
      }
      const categoryId = parseInt(rootElement.dataset.categoryId, 10);
      const lang = rootElement.dataset.lang;
      await setMomentLocale(lang);
      ReactDOM.render(
        <LocaleContext.Provider value={lang}>
          <CategoryStatistics categoryId={categoryId} />
        </LocaleContext.Provider>,
        rootElement
      );
    });
  };
})(window);
