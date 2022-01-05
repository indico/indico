// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  'use strict';

  global.setupSyncedInputWidget = function setupSyncedInputWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
      },
      options
    );

    $('#' + options.fieldId + '-action-button').on('click', function() {
      var field = $('#' + options.fieldId);
      var syncedValue;

      field.prop('readonly', this.checked);
      if (this.checked) {
        syncedValue = JSON.parse(field.attr('data-synced-value'));
        if (syncedValue !== null) {
          field.val(syncedValue);
        }
      }
    });
  };
})(window);
