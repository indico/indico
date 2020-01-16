// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global setupListGenerator:false, setupTableSorter:false, setupSearchBox:false, enableIfChecked:false */

import 'indico/modules/events/reviews';

import setupReactPaperTimeline from './setup';

(function(global) {
  'use strict';

  global.setupPaperAssignmentList = function setupPaperAssignmentList() {
    const filterConfig = {
      itemHandle: 'tr',
      listItems: '#assignment-list tbody tr',
      term: '#search-input',
      state: '#filtering-state',
      placeholder: '#filter-placeholder',
    };

    setupTableSorter('#assignment-list .tablesorter');
    enableIfChecked('#assignment-list', 'input[name=contribution_id]', '.js-enable-if-checked');
    setupListGenerator(filterConfig);
  };

  global.setupReviewingAreaList = function setupReviewingAreaList(options) {
    options = $.extend(
      {
        hasPapers: false,
      },
      options
    );

    if (options.hasPapers) {
      let filterConfig = {
        itemHandle: 'div.contribution-row',
      };
      if (options.list === 'to-review') {
        filterConfig = $.extend(
          {
            listItems: '#to-review-list div.contribution-row',
            term: '#search-input-to-review',
            state: '#filtering-state-to-review',
            placeholder: '#filter-placeholder-to-review',
          },
          filterConfig
        );
      } else {
        filterConfig = $.extend(
          {
            listItems: '#reviewed-list div.contribution-row',
            term: '#search-input-reviewed',
            state: '#filtering-state-reviewed',
            placeholder: '#filter-placeholder-reviewed',
          },
          filterConfig
        );
      }
      const applySearchFilters = setupSearchBox(filterConfig);
      applySearchFilters();
    }
  };

  global.setupCallForPapersPage = function setupCallForPapersPage(options) {
    if (options.hasPapers) {
      const filterConfig = {
        itemHandle: 'div.contribution-row',
        listItems: 'div.paper-contribution-list div.contribution-row',
        term: '#search-input',
        state: '#filtering-state',
        placeholder: '#filter-placeholder',
      };

      const applySearchFilters = setupSearchBox(filterConfig);
      applySearchFilters();
    }
  };
})(window);

document.addEventListener('DOMContentLoaded', () => {
  setupReactPaperTimeline();
});
