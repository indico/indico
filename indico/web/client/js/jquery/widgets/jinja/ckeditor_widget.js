// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import ClassicEditor from 'ckeditor';
import {getConfig} from 'indico/ckeditor';

(function(global) {
  'use strict';

  global.setupCKEditorWidget = async function setupCKEditorWidget(options) {
    const {fieldId, images = false, height = 475, ...rest} = options;

    const field = document.getElementById(fieldId);
    const editor = await ClassicEditor.create(field, {...getConfig({images}), ...rest});
    editor.setData(field.value);
    editor.model.document.on('change:data', () => {
      field.value = editor.getData();
      field.dispatchEvent(new Event('change'));
    });
  };
})(window);
