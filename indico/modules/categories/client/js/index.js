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
import {setMomentLocale} from 'indico/utils/date';

import CategoryStatistics from './components/CategoryStatistics';
import {LocaleContext} from './context.js';

(function(global) {
  document.addEventListener('DOMContentLoaded', () => {
    const domContainer = document.querySelector('#search-box');

    if (domContainer) {
      const category = JSON.parse(domContainer.dataset.category);

      ReactDOM.render(
        React.createElement(SearchBox, {
          onSearch: (keyword, isGlobal) => {
            if (isGlobal) {
              window.location = searchUrl({q: keyword});
            } else {
              window.location = categorySearchUrl({category_id: category.id, q: keyword});
            }
          },
          category,
        }),
        domContainer
      );
    }
  });
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
