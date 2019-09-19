// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import searchUrl from 'indico-url:search.search';

import React from 'react';
import ReactDOM from 'react-dom';
import SearchBar from 'indico/modules/search/components/SearchBar';
import {setMomentLocale} from 'indico/utils/date';
import CategoryStatistics from './components/CategoryStatistics';
import {LocaleContext} from './context.js';
import './display';

(function(global) {
  document.addEventListener('DOMContentLoaded', () => {
    const domContainer = document.querySelector('#search-box');
    ReactDOM.render(
      React.createElement(SearchBar, {
        onSearch: keyword => {
          window.location = searchUrl({q: keyword});
        },
        searchTerm: '',
      }),
      domContainer
    );
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
