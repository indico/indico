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
        var $trackList = $('#track-list');

        $trackList.find('.track-content').each(function() {
          var $this = $(this);
          if ($this.height() > heightLimit) {
            $this.addClass('track-content-collapsed track-content-collapsible');
            $this.on('click', function() {
              $this.toggleClass('track-content-collapsed');
            });
          }
        });

        $trackList.sortable({
          axis: 'y',
          containment: 'parent',
          cursor: 'move',
          distance: 2,
          handle: '.ui-i-box-sortable-handle',
          items: '> li.track-row',
          tolerance: 'pointer',
          forcePlaceholderSize: true,
          update: function() {
            var sortedList = $trackList
              .find('li.track-row')
              .map(function() {
                return $(this).data('id');
              })
              .get();

            $.ajax({
              url: $trackList.data('url'),
              method: 'POST',
              contentType: 'application/json',
              data: JSON.stringify({sort_order: sortedList}),
              complete: IndicoUI.Dialogs.Util.progress(),
              error: handleAjaxError,
            });
          },
        });
      })
      .trigger('indico:htmlUpdated');
  };
})(window);
