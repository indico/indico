// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

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

    _create: function() {
      var self = this;
      var classes = self.options.style ? self.options.style.classes : '';

      self.element.qtip(
        $.extend(true, {}, self.defaultQtipOptions, self.options, {
          style: {classes: 'qbubble ' + classes},
        })
      );

      this._on({
        click: function(evt) {
          evt.preventDefault();
        },
      });
    },

    api: function() {
      var self = this;
      return self.element.qtip('api');
    },

    destroy: function() {
      var self = this;
      self.element.qtip('destroy');
    },

    hide: function() {
      var self = this;
      self.element.qtip('hide');
    },

    option: function(entry, value) {
      var self = this;
      self.element.qtip('option', entry, value);
    },

    createNested: function(elem, nestedQtipOptions) {
      var self = this;
      var originalHideCallback = nestedQtipOptions.events && nestedQtipOptions.events.hide;
      var originalShowCallback = nestedQtipOptions.events && nestedQtipOptions.events.show;
      $.extend(true, nestedQtipOptions, {
        events: {
          show: function(evt, api) {
            if (originalShowCallback) {
              originalShowCallback(evt, api);
            }
            if (!evt.defaultPrevented) {
              self._hasNestedOpen = true;
              self.element.qtip('disable');
            }
          },
          hide: function(evt, api) {
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
