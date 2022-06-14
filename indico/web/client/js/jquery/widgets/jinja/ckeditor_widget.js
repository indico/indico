// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import ClassicEditor from 'ckeditor';

import {getConfig} from 'indico/ckeditor';

(function(global) {
  global.setupCKEditorWidget = async function setupCKEditorWidget(options) {
    const {fieldId, simple = true, images = false, width, height = 475, ...rest} = options;
    const field = document.getElementById(fieldId);
    const editor = await ClassicEditor.create(field, {...getConfig({simple, images}), ...rest});
    editor.setData(field.value);
    editor.model.document.on('change:data', () => {
      field.value = editor.getData();
      field.dispatchEvent(new Event('change', {bubbles: true}));
    });
    editor.editing.view.change(writer => {
      writer.setStyle('width', `${width}px` || 'auto', editor.editing.view.document.getRoot());
      writer.setStyle('height', `${height}px`, editor.editing.view.document.getRoot());
    });
    // Re-position the dialog if we have one since the initial position is
    // wrong due to the editor being loaded after the dialog has been opened.
    const dialog = $(field.closest('.ui-dialog-content'));
    if (dialog.length) {
      dialog.dialog('option', 'position', dialog.dialog('option', 'position'));
    }
    // Make sure the option dropdowns are displayed above the dialog.
    const uiDialog = field.closest('.ui-dialog-content');
    const exPopup = field.closest('.exclusivePopup');
    if (uiDialog) {
      uiDialog.style.overflow = 'inherit';
    }
    if (exPopup) {
      exPopup.style.overflow = 'inherit';
    }
  };
})(window);
