// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global setupListGenerator:false, setupTableSorter:false, setupSearchBox:false, enableIfChecked:false */

import 'indico/modules/events/reviews';

import setupReactPaperTimeline from './setup';

(function(global) {
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

    $('#assignment-list .tablesorter').on(
      'mouseover',
      '.title-column .vertical-aligner, .track-column .vertical-aligner',
      function() {
        const title = $(this);
        // Show a qtip if the text is ellipsized
        if (this.offsetWidth < this.scrollWidth) {
          title.qtip({hide: 'mouseout', content: title.text(), overwrite: false}).qtip('show');
        }
      }
    );
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

  global.setupConflictsList = function setupConflictsList() {
    const $conflictListTooltip = $('.js-assign-dialog .name-column .affiliation > span');
    $conflictListTooltip.qbubble({
      show: {
        event: 'mouseover',
      },
      hide: {
        fixed: true,
        delay: 100,
        event: 'mouseleave',
      },
      position: {
        my: 'left center',
        at: 'right center',
      },
      content: {
        text() {
          const $this = $(this);
          const html = $('<div>');
          const title = $('<strong>', {text: $(this).data('title')});
          html.append(title);
          if ($this.is('.js-count-label')) {
            const list = $('<ul>', {class: 'qbubble-item-list'});
            const items = Object.values($this.data('items'));
            $.each(items, function(i, val) {
              const item = $('<li>');
              item.append(
                $('<a>', {text: val[0], href: val[1]})
                  .attr('target', '_blank')
                  .attr('rel', 'noopener noreferrer')
              );
              list.append(item);
            });
            html.append(list);
          }
          return html;
        },
      },
    });
  };
})(window);

document.addEventListener('DOMContentLoaded', () => {
  setupReactPaperTimeline();
});
