// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  'use strict';

  global.setupOverrideMultipleItemsWidget = function setupOverrideMultipleItemsWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
      },
      options
    );

    var widget = $('#' + options.fieldId + '-widget');
    var field = $('#' + options.fieldId);
    var data = JSON.parse(field.val());

    widget.on('input change', 'input', function() {
      var $this = $(this);
      if (data[$this.data('key')] === undefined) {
        data[$this.data('key')] = {};
      }
      data[$this.data('key')][$this.data('field')] = $this.val();
      updateField();
    });

    widget.find('input').each(function() {
      var $this = $(this);
      var rowData = data[$this.data('key')] || {};
      $this.val(rowData[$this.data('field')] || '');
    });

    function updateField() {
      field.val(JSON.stringify(data));
    }
  };
})(window);
