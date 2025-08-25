// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */

(function($) {
  $.widget('indico.clearableinput', {
    options: {
      alwaysClearable: false,
      clearClass: 'clearableinput',
      clearOnEscape: true,
      emptyvalue: '',
      focusOnClear: true,
      focusOnStart: false,
      onClear() {},
      onInput() {},
    },

    _create() {
      const self = this;

      self.buttonBox = $('<span>').addClass('button-box');
      self.clearIcon = $('<a>')
        .addClass('i-link danger icon-close')
        .click(evt => {
          self._clear();
          evt.stopPropagation();
        });

      const wrapper = $('<span>').addClass(self.options.clearClass);
      self.element
        .addClass('clearabletext')
        .wrap(wrapper)
        .on('input', () => {
          self._handleInput();
        })
        .on('keyup', e => {
          if (self.options.clearOnEscape) {
            if (e.key === 'Escape') {
              self.element.val('value');
              self._clear();
            }
          }
        });

      self.buttonBox.append(self.clearIcon);
      self.element.after(self.buttonBox);
      self._refreshClearIcon();

      if (self.options.focusOnStart) {
        self.element.focus();
      }
    },

    _clear() {
      const self = this;
      self.element.val(self.options.emptyvalue).trigger('propertychange').trigger('change');
      self._refreshClearIcon();
      self.options.onClear.call(self.element);
      if (self.options.focusOnClear) {
        self.element.focus();
      } else {
        self.element.blur();
      }
    },

    _handleInput() {
      const self = this;
      self.options.onInput.call(self.element);
      self._refreshClearIcon();
    },

    _refreshClearIcon() {
      const self = this;
      if (self.element.val() === self.options.emptyvalue && !self.options.alwaysClearable) {
        self.clearIcon.css('visibility', 'hidden');
      } else {
        self.clearIcon.css('visibility', 'visible');
      }
    },

    initSize(fontSize, lineHeight) {
      const self = this;
      if (self.size === undefined) {
        self.size = {
          fontSize,
          lineHeight,
        };
      }
      self.clearIcon.css('font-size', self.size.fontSize);
      self.clearIcon.css('line-height', self.size.lineHeight);
      self.element.css('min-height', self.size.lineHeight);
    },

    setEmptyValue(value) {
      const self = this;
      self.options.emptyvalue = value;
    },

    setValue(value) {
      const self = this;
      self.element.val(value);
      self._refreshClearIcon();
    },

    setIconsVisibility(visibility) {
      const self = this;
      self.clearIcon.css('visibility', visibility);
    },
  });
})(jQuery);
