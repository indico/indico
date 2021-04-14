// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function(global) {
  global.setupColorPickerWidget = function setupColorPickerWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
        showField: true,
      },
      options
    );

    var $formField = $('#' + options.fieldId);
    var $colorField = $formField.closest('.i-color-field');

    $colorField.indicoColorpicker();
    if (options.showField) {
      $formField.clearableinput({
        focusOnClear: false,
        onClear: () => {
          $colorField.indicoColorpicker('updateWidget');
        },
      });
    } else {
      $formField.hide();
    }

    // Hack to set clearable input whenever the color changes
    $formField
      .on('change', () => {
        $formField.clearableinput('setValue', $formField.val());
      })
      .on('cancel', () => {
        $formField.clearableinput('setValue', $formField.val());
      });
  };
})(window);
