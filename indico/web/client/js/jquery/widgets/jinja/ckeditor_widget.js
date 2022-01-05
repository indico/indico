// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global RichTextEditor:false, $E:false */

(function(global) {
  'use strict';

  global.setupCKEditorWidget = function setupCKEditorWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
        simple: false,
        images: false,
        height: 475,
      },
      options
    );

    var field = $('#' + options.fieldId);
    var editor = new RichTextEditor(600, options.height, options.simple, options.images);
    editor.set(field.val());
    editor.onLoad(function() {
      editor.onChange(function() {
        field.val(editor.get()).trigger('change');
      });
    });
    $E(options.fieldId + '-editor').set(editor.draw());
    // Re-position the dialog if we have one since the initial position is
    // wrong due to the editor being loaded after the dialog has been opened.
    var dialog = field.closest('.ui-dialog-content');
    if (dialog.length) {
      dialog.dialog('option', 'position', dialog.dialog('option', 'position'));
    }
  };
})(window);
