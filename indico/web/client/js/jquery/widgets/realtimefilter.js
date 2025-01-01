// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'jquery.typewatch';

(function($) {
  $.widget('indico.realtimefilter', {
    options: {
      callback: function() {},
      validation: function() {
        return true;
      },
      clearable: true,
      disableenter: true,
      emptyvalue: '',
      invalidclass: 'invalid',
      wait: 250,
    },

    _create: function() {
      var self = this;
      var element = self.element;
      var opt = self.options;

      element.typeWatch({
        callback: function() {
          self._callback();
        },
        wait: opt.wait,
        highlight: false,
        captureLength: 0,
      });

      if (opt.clearable) {
        element.clearableinput({
          onClear: function() {
            self._callback();
          },
          emptyvalue: opt.emptyvalue,
        });
      }

      element.on('cut paste', function() {
        self._delayedCallback();
      });

      element.on('focusout', function() {
        if ($(this).val() === '') {
          $(this).val(opt.emptyvalue);
        }
      });

      if (opt.disableenter) {
        element.on('keydown', function(e) {
          if (e.key === 'Enter') {
            e.preventDefault();
          }
        });
      }
    },

    _callback: function() {
      var self = this;
      var element = self.element;
      var opt = self.options;

      if (opt.validation(element)) {
        element.removeClass(opt.invalidclass);
        opt.callback(element.val().trim());
      } else {
        element.addClass(opt.invalidclass);
      }
    },

    _delayedCallback: function() {
      var self = this;

      setTimeout(function() {
        self._callback();
      }, self.options.wait);
    },

    clear: function() {
      var self = this;
      self.setValue('');
    },

    setValue: function(value) {
      var self = this;
      if (self.options.clearable) {
        self.element.clearableinput('setValue', value);
      } else {
        self.element.val(value);
      }
      // Needed for typeWatch to refresh its timer
      self.element.trigger('input');
    },

    update: function(delayed) {
      var self = this;

      if (delayed) {
        self._delayedCallback();
      } else {
        self._callback();
      }
    },

    validate: function() {
      var self = this;
      return self.options.validation(self.element);
    },
  });
})(jQuery);
