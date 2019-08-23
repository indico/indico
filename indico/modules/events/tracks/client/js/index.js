// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  'use strict';

  global.setupTrackManagement = function setupTrackManagement() {
    var heightLimit = 50;
    $('#track-list-container')
      .on('indico:htmlUpdated', function() {
        const $this = $(this);
        $this.find('.track-list .track-content').each(function() {
          if ($this.height() > heightLimit) {
            $this.addClass('track-content-collapsed track-content-collapsible');
            $this.on('click', function() {
              $this.toggleClass('track-content-collapsed');
            });
          }
        });

        $this.find('.track-list').sortable({
          items: '.track-row',
          handle: '.ui-i-box-sortable-handle',
          axis: 'y',
          cursor: 'move',
          distance: 2,
          tolerance: 'pointer',
          forcePlaceholderSize: true,
          connectWith: '.track-list',
          update: function() {
            const $this = $(this);
            const sortedList = $this.find('li.track-row')
              .map(function() {
                const $this = $(this);
                if ($this.hasClass('track-group-box')) {
                  return {id: $this.data('id'), type: 'group'};
                } else {
                  let parent = null;
                  const parentDiv = $this.closest('.track-group-box');
                  if (parentDiv.length) {
                    parent = parentDiv.data('id');
                  }
                  return {id: $this.data('id'), type: 'track', parent};
                }
              })
              .get();
            $.ajax({
              url: $this.data('url'),
              method: 'POST',
              contentType: 'application/json',
              data: JSON.stringify({sort_order: sortedList}),
              complete: IndicoUI.Dialogs.Util.progress(),
              error: handleAjaxError,
            });
          },
          receive: function(event, ui) {
            const parentDiv = $this.closest('.track-group-box');
            if (parentDiv.length && ui.item.hasClass('track-group-box')) {
              $(ui.sender).sortable('cancel');
            }
          }
      });
    })
    .trigger('indico:htmlUpdated');
  }
})(window);
