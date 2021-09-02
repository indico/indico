// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import categorySearchUrl from 'indico-url:search.category_search';
import searchUrl from 'indico-url:search.search';

import React from 'react';
import ReactDOM from 'react-dom';

import './display';
import './base';

import SearchBox from 'indico/modules/search/components/SearchBox';

import CategoryStatistics from './components/CategoryStatistics';
import {LocaleContext} from './context.js';

(function(global) {
  document.addEventListener('DOMContentLoaded', () => {
    const domContainer = document.querySelector('#search-box');

    if (domContainer) {
      const category = JSON.parse(domContainer.dataset.category);
      const isAdmin = domContainer.dataset.isAdmin !== undefined;

      ReactDOM.render(
        React.createElement(SearchBox, {
          onSearch: (keyword, isGlobal, adminOverrideEnabled) => {
            const params = {q: keyword};
            if (isAdmin && adminOverrideEnabled) {
              params.admin_override_enabled = true;
            }
            if (isGlobal) {
              window.location = searchUrl(params);
            } else {
              params.category_id = category.id;
              window.location = categorySearchUrl(params);
            }
          },
          category,
          isAdmin,
        }),
        domContainer
      );
    }
  });
  global.setupCategoryStats = function setupCategoryStats() {
    document.addEventListener('DOMContentLoaded', () => {
      const rootElement = document.querySelector('#category-stats-root');
      if (!rootElement) {
        return;
      }
      const categoryId = parseInt(rootElement.dataset.categoryId, 10);
      const lang = rootElement.dataset.lang;
      ReactDOM.render(
        <LocaleContext.Provider value={lang}>
          <CategoryStatistics categoryId={categoryId} />
        </LocaleContext.Provider>,
        rootElement
      );
    });
  };
})(window);
