// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */

(function($) {
  $.widget('indico.scrollblocker', {
    options: {
      overflowType: 'scroll',
    },

    _create() {
      const element = this.element;
      const options = this.options;

      $('body').on('mousewheel wheel', e => {
        const blocker = $(e.target)
          .parentsUntil(element.parent())
          .filter(function() {
            return $(this).hasCSS('overflow-y', options.overflowType);
          });

        if (blocker.length > 0) {
          const wheelup = (e.originalEvent.wheelDelta || -e.originalEvent.deltaY) / 120 > 0;

          if (blocker.scrollTop() === 0 && wheelup) {
            return false;
          }

          if (
            blocker.scrollTop() + 1 >= blocker.prop('scrollHeight') - blocker.outerHeight() &&
            !wheelup
          ) {
            return false;
          }
        }

        return true;
      });
    },
  });
})(jQuery);
