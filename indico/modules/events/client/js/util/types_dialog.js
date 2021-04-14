// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  global.setupTypesDialog = function setupTypesDialog() {
    var $manageTypes = $('.manage-types');

    /* Set the customData to true indicating that the list needs to be refreshed */
    function dialogModified() {
      $manageTypes.trigger('ajaxDialog:setData', [true]);
    }

    $('.manage-types table').tablesorter({
      sortList: [[0, 0]],
      headers: {
        2: {
          sorter: false,
        },
      },
    });

    $('.js-new-type').on('ajaxDialog:closed', function(evt, data) {
      evt.preventDefault();
      if (data) {
        var $lastRow = $('.manage-types table tr:last');
        if ($lastRow.length) {
          $lastRow.after(data.html_row);
          dialogModified();
        } else {
          $manageTypes.trigger('ajaxDialog:reload');
        }
      }
    });

    $manageTypes.on('ajaxDialog:closed', '.js-edit-type', function(evt, data) {
      evt.preventDefault();
      if (data) {
        var $row = $(this).closest('tr');
        $row.replaceWith(data.html_row);
        dialogModified();
      }
    });

    $manageTypes.on('indico:confirmed', '.js-delete-type', function(evt) {
      evt.preventDefault();
      var $this = $(this);
      $.ajax({
        url: $this.data('href'),
        method: $this.data('method'),
        complete: IndicoUI.Dialogs.Util.progress(),
        error: handleAjaxError,
        success: function() {
          var $row = $this.closest('tr');
          $row.remove();
          dialogModified();
          if ($('.manage-types table tbody tr').length === 0) {
            $manageTypes.trigger('ajaxDialog:reload');
          }
        },
      });
    });
  };
})(window);
