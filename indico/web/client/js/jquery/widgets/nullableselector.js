// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function($) {
  'use strict';

  $.widget('indico.nullableselector', {
    options: {
      nullvalue: '__None',
    },

    _create: function() {
      var self = this;
      var element = self.element;
      var opt = self.options;

      element.toggleClass('no-value', element.val() === opt.nullvalue);
      element.on('change', function() {
        $(this).toggleClass('no-value', $(this).val() === opt.nullvalue);
      });
    },
  });
})(jQuery);
