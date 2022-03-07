// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  let totalDurationDisplay;

  function formatState(visible, total) {
    return '{0} / {1}'.format('<strong>{0}</strong>'.format(visible.length), total.length);
  }

  function setState(state, visible, total) {
    state.html($('<span>').append(formatState(visible, total)));
    state.attr(
      'title',
      $T.gettext('{0} out of {1} displayed').format(visible.length, total.length)
    );
    if (!totalDurationDisplay) {
      totalDurationDisplay = $('#total-duration').detach();
    }
  }

  function _applySearchFilters(searchBoxConfig) {
    const childHandles = searchBoxConfig.childHandles || '.details-row';
    const $itemsWithChild = $(searchBoxConfig.listItems);
    const $items = $itemsWithChild.not(childHandles);
    let term = $(searchBoxConfig.term).val();
    const $state = $(searchBoxConfig.state);
    let $visibleEntries, m;
    const $filterPlaceholder = $(searchBoxConfig.placeholder);

    if (!term) {
      if ($state.hasClass('active')) {
        $itemsWithChild.show();
      }

      $state.removeClass('active');
      setState($state, $items, $items);
      if (totalDurationDisplay) {
        $state.after(totalDurationDisplay);
        totalDurationDisplay = null;
      }
      return;
    }

    // quick search of contribution by ID
    term = term.trim();
    if ((m = term.match(/^#(\d+)$/))) {
      $visibleEntries = $items.filter(`[data-friendly-id="${m[1]}"]`);
    } else {
      $visibleEntries = $items
        .find(`[data-searchable*="${term.toLowerCase()}"]`)
        .closest(searchBoxConfig.itemHandle);
    }

    if ($visibleEntries.length === 0) {
      $filterPlaceholder
        .text($T.gettext('There are no entries that match your search criteria.'))
        .show();
      $state.addClass('active');
    } else {
      $filterPlaceholder.hide();
      if ($visibleEntries.length !== $items.length) {
        $state.addClass('active');
      }
    }

    setState($state, $visibleEntries, $items);

    $itemsWithChild.hide();
    $visibleEntries.show();
    $visibleEntries.next(childHandles).show();

    // Needed because $(window).scroll() is not called when hiding elements
    // causing scrolling elements to be out of place.
    $(window).trigger('scroll');
  }

  global.setupSearchBox = function setupSearchBox(config) {
    const applySearchFilters = _.partial(_applySearchFilters, config);
    const $term = $(config.term);

    if ($term.length) {
      $term.realtimefilter({
        callback: applySearchFilters,
      });
    }

    // make sure that filters are applied when e.g. going back in
    // browser history, this is needed since typewatch, which is used internally
    // by realtimefilter, calls applySearchFilter only when user is typing
    applySearchFilters();
    return applySearchFilters;
  };
})(window);
