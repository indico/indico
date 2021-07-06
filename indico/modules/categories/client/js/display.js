// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global handleAjaxError:false */

import {$T} from 'indico/utils/i18n';

(function(global) {
  global.setupCategoryDisplaySubcatList = function setupCategoryDisplaySubcatList() {
    const url = $('.category-list').data('subcat-info-url');
    if (url === undefined) {
      // there's no .category-list if there are no subcategories
      return;
    }
    $.ajax({
      url,
      dataType: 'json',
      success(data) {
        Object.entries(data.event_counts).forEach(([id, count]) => {
          const text = !count.value
            ? $T.gettext('empty')
            : $T.ngettext('{0} event', '{0} events', count.value).format(count.pretty);
          $(`#category-event-count-${id}`).text(text);
        });
      },
    });
  };

  global.setupCategoryDisplayEventList = function setupCategoryDisplayEventList(
    showFutureEvents,
    showPastEvents,
    isFlat,
    requestParams
  ) {
    const $eventList = $('.event-list');
    const $futureEvents = $eventList.find('.future-events');
    const $pastEvents = $eventList.find('.past-events');

    if (isFlat) {
      requestParams.flat = 1;
    }

    setupToggleEventListButton($futureEvents, onToggleFutureEvents);
    setupToggleEventListButton($pastEvents, onTogglePastEvents);

    if (showFutureEvents && !isFlat) {
      $futureEvents
        .find('.js-toggle-list')
        .first()
        .trigger('click', true);
    }

    if (showPastEvents && !isFlat) {
      $pastEvents
        .find('.js-toggle-list')
        .first()
        .trigger('click', true);
    }

    function onToggleFutureEvents(shown) {
      if (isFlat) {
        return;
      }
      $.ajax({
        url: $eventList.data('show-future-events-url'),
        method: shown ? 'PUT' : 'DELETE',
        error: handleAjaxError,
      });
    }

    function onTogglePastEvents(shown) {
      if (isFlat) {
        return;
      }
      $.ajax({
        url: $eventList.data('show-past-events-url'),
        method: shown ? 'PUT' : 'DELETE',
        error: handleAjaxError,
      });
    }

    function setupToggleEventListButton(wrapper, callback) {
      const $wrapper = $(wrapper);
      const $content = $wrapper.find('.events');

      function updateMessage(visible) {
        $wrapper.find('.js-hide-message').toggle(visible);
        $wrapper.find('.js-show-message').toggle(!visible);
      }
      updateMessage(!$content.is(':empty'));

      function displaySpinner(visible) {
        $wrapper.find('.js-toggle-list').toggle(!visible);
        $wrapper.find('.js-spinner').toggle(visible);
      }
      displaySpinner(false);

      $wrapper.find('.js-toggle-list').on('click', function(evt, triggeredAutomatically) {
        evt.preventDefault();
        let visible;
        if ($content.is(':empty')) {
          visible = true;
          displaySpinner(true);
          $.ajax({
            url: $content.data('event-list-url'),
            data: {
              before: $content.data('event-list-before'),
              after: $content.data('event-list-after'),
              ...requestParams,
            },
            error: handleAjaxError,
            success(data) {
              $content.html(data.html);
              $content.show();
              updateMessage(true);
              displaySpinner(false);
            },
          });
        } else if ($content.is(':visible')) {
          visible = false;
          $content.hide();
          updateMessage(false);
        } else {
          visible = true;
          $content.show();
          updateMessage(true);
        }
        if (!triggeredAutomatically && callback) {
          callback(visible);
        }
      });
    }
  };

  global.setupCategoryDisplay = function setupCategoryDisplay() {
    $('.fav-button')
      .on('click', function() {
        const $this = $(this);
        const isFavorite = $this.hasClass('enabled');
        $this.prop('disabled', true);
        $.ajax({
          url: $this.data('href'),
          method: isFavorite ? 'DELETE' : 'PUT',
          error: handleAjaxError,
          success() {
            $this.toggleClass('enabled', !isFavorite);
          },
          complete() {
            $this.prop('disabled', false);
          },
        });
      })
      .qtip({
        hide: {
          fixed: true,
          delay: 500,
        },
        content: {
          text() {
            const $this = $(this);
            if ($this.hasClass('enabled')) {
              return $T.gettext('Remove from your favorites');
            } else {
              return '<h3>{0}</h3><p>{1}</p>'.format(
                $T.gettext('Add to your favorites'),
                $T
                  .gettext(
                    'This will make events in this category visible on your <a href="{0}">Dashboard</a>.'
                  )
                  .format($this.data('favorites-href'))
              );
            }
          },
        },
      });
  };
})(window);
