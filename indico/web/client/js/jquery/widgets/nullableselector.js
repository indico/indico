// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */

(function($) {
  $.widget('indico.nullableselector', {
    options: {
      nullvalue: '__None',
    },

    _create() {
      const self = this;
      const element = self.element;
      const opt = self.options;

      element.toggleClass('no-value', element.val() === opt.nullvalue);
      element.on('change', function() {
        $(this).toggleClass('no-value', $(this).val() === opt.nullvalue);
      });
    },
  });
})(jQuery);
