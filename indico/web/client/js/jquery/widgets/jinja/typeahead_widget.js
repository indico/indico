// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'jquery-typeahead';
import 'jquery-typeahead/src/jquery.typeahead.css';

(function(global) {
  global.setupTypeaheadWidget = function setupTypeaheadWidget(options) {
    options = $.extend(
      true,
      {
        fieldId: null,
        minTriggerLength: 0,
        data: null,
        typeaheadOptions: null,
        searchUrl: null,
      },
      options
    );

    const field = $(`#${options.fieldId}`);
    const params = {
      hint: true,
      cancelButton: false,
      mustSelectItem: true,
      minLength: options.minTriggerLength,
      source: {
        data: options.data,
      },
    };

    if (options.searchUrl) {
      $.extend(true, params, {
        dynamic: true,
        source: {
          url: [
            {
              url: options.searchUrl,
              data: {
                q: '{{query}}',
              },
            },
          ],
        },
      });
    }

    field.typeahead($.extend(true, params, options.typeaheadOptions));
  };
})(window);
