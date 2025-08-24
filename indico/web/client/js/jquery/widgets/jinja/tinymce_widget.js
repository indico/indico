// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import tinymce from 'tinymce/tinymce';

import {getConfig} from 'indico/tinymce';

(function(global) {
  global.setupTinyMCEWidget = async function setupTinyMCEWidget(options) {
    const {
      fieldId,
      disabled = false,
      images = true,
      imageUploadURL = null,
      forceAbsoluteURLs = false,
      height = 475,
    } = options;
    const contentCSS = JSON.parse(document.body.dataset.tinymceContentCss);

    const field = document.getElementById(fieldId);
    const old = tinymce.get(fieldId);
    if (old) {
      // TinyMCE keeps a list of instances by field ID, and without removing the old one
      // creating a new one on the same ID (e.g. inside a lazy-loaded dialog that's been
      // closed and then reopened) won't do anything
      tinymce.remove(old);
    }
    tinymce.init(
      getConfig(field, {disabled, images, imageUploadURL, forceAbsoluteURLs, height, contentCSS})
    );
  };
})(window);
