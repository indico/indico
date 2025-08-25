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
      callback() {},
      validation() {
        return true;
      },
      clearable: true,
      disableenter: true,
      emptyvalue: '',
      invalidclass: 'invalid',
      wait: 250,
    },

    _create() {
      const self = this;
      const element = self.element;
      const opt = self.options;

      element.typeWatch({
        callback() {
          self._callback();
        },
        wait: opt.wait,
        highlight: false,
        captureLength: 0,
      });

      if (opt.clearable) {
        element.clearableinput({
          onClear() {
            self._callback();
          },
          emptyvalue: opt.emptyvalue,
        });
      }

      element.on('cut paste', () => {
        self._delayedCallback();
      });

      element.on('focusout', function() {
        if ($(this).val() === '') {
          $(this).val(opt.emptyvalue);
        }
      });

      if (opt.disableenter) {
        element.on('keydown', e => {
          if (e.key === 'Enter') {
            e.preventDefault();
          }
        });
      }
    },

    _callback() {
      const self = this;
      const element = self.element;
      const opt = self.options;

      if (opt.validation(element)) {
        element.removeClass(opt.invalidclass);
        opt.callback(element.val().trim());
      } else {
        element.addClass(opt.invalidclass);
      }
    },

    _delayedCallback() {
      const self = this;

      setTimeout(() => {
        self._callback();
      }, self.options.wait);
    },

    clear() {
      const self = this;
      self.setValue('');
    },

    setValue(value) {
      const self = this;
      if (self.options.clearable) {
        self.element.clearableinput('setValue', value);
      } else {
        self.element.val(value);
      }
      // Needed for typeWatch to refresh its timer
      self.element.trigger('input');
    },

    update(delayed) {
      const self = this;

      if (delayed) {
        self._delayedCallback();
      } else {
        self._callback();
      }
    },

    validate() {
      const self = this;
      return self.options.validation(self.element);
    },
  });
})(jQuery);
