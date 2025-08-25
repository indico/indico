// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */

(function($) {
  $.widget('indico.qbubble', {
    defaultQtipOptions: {
      overwrite: true,
      suppress: false,
      position: {
        my: 'top center',
        at: 'bottom center',
        adjust: {
          mouse: false,
          scroll: false,
        },
      },
      show: {
        event: 'click',
        solo: true,
      },
      hide: {
        event: 'unfocus click',
      },
    },

    _create() {
      const self = this;
      const classes = self.options.style ? self.options.style.classes : '';

      self.element.qtip(
        $.extend(true, {}, self.defaultQtipOptions, self.options, {
          style: {classes: `qbubble ${classes}`},
        })
      );

      this._on({
        click(evt) {
          evt.preventDefault();
        },
      });
    },

    api() {
      const self = this;
      return self.element.qtip('api');
    },

    destroy() {
      const self = this;
      self.element.qtip('destroy');
    },

    hide() {
      const self = this;
      self.element.qtip('hide');
    },

    option(entry, value) {
      const self = this;
      self.element.qtip('option', entry, value);
    },

    createNested(elem, nestedQtipOptions) {
      const self = this;
      const originalHideCallback = nestedQtipOptions.events && nestedQtipOptions.events.hide;
      const originalShowCallback = nestedQtipOptions.events && nestedQtipOptions.events.show;
      $.extend(true, nestedQtipOptions, {
        events: {
          show(evt, api) {
            if (originalShowCallback) {
              originalShowCallback(evt, api);
            }
            if (!evt.defaultPrevented) {
              self._hasNestedOpen = true;
              self.element.qtip('disable');
            }
          },
          hide(evt, api) {
            if (originalHideCallback) {
              originalHideCallback(evt, api);
            }
            if (!evt.defaultPrevented) {
              self._hasNestedOpen = false;
              self.element.qtip('enable');
            }
          },
        },
      });
      elem.qbubble(nestedQtipOptions);
    },
  });
})(jQuery);
