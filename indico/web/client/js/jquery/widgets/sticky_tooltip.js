// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */

(function($, global) {
  $.fn.stickyTooltip = function(category, content) {
    return this.qtip({
      content: {
        text: content,
      },
      position: {
        my: 'left middle',
        at: 'middle right',
      },
      hide: {
        event: 'click unfocus',
      },
      style: {
        classes: `qtip-${category}`,
      },
      show: {
        when: false,
        ready: true,
      },
    });
  };

  global.repositionTooltips = function repositionTooltips() {
    $('.qtip').qtip('reposition');
  };
})(jQuery, window);
