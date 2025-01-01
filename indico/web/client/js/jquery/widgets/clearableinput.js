// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function($) {
  'use strict';

  $.widget('indico.clearableinput', {
    options: {
      alwaysClearable: false,
      clearClass: 'clearableinput',
      clearOnEscape: true,
      emptyvalue: '',
      focusOnClear: true,
      focusOnStart: false,
      onClear: function() {},
      onInput: function() {},
    },

    _create: function() {
      var self = this;

      self.buttonBox = $('<span>').addClass('button-box');
      self.clearIcon = $('<a>')
        .addClass('i-link danger icon-close')
        .click(function(evt) {
          self._clear();
          evt.stopPropagation();
        });

      var wrapper = $('<span>').addClass(self.options.clearClass);
      self.element
        .addClass('clearabletext')
        .wrap(wrapper)
        .on('input', function() {
          self._handleInput();
        })
        .on('keyup', function(e) {
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

    _clear: function() {
      var self = this;
      self.element
        .val(self.options.emptyvalue)
        .trigger('propertychange')
        .trigger('change');
      self._refreshClearIcon();
      self.options.onClear.call(self.element);
      if (self.options.focusOnClear) {
        self.element.focus();
      } else {
        self.element.blur();
      }
    },

    _handleInput: function() {
      var self = this;
      self.options.onInput.call(self.element);
      self._refreshClearIcon();
    },

    _refreshClearIcon: function() {
      var self = this;
      if (self.element.val() === self.options.emptyvalue && !self.options.alwaysClearable) {
        self.clearIcon.css('visibility', 'hidden');
      } else {
        self.clearIcon.css('visibility', 'visible');
      }
    },

    initSize: function(fontSize, lineHeight) {
      var self = this;
      if (self.size === undefined) {
        self.size = {
          fontSize: fontSize,
          lineHeight: lineHeight,
        };
      }
      self.clearIcon.css('font-size', self.size.fontSize);
      self.clearIcon.css('line-height', self.size.lineHeight);
      self.element.css('min-height', self.size.lineHeight);
    },

    setEmptyValue: function(value) {
      var self = this;
      self.options.emptyvalue = value;
    },

    setValue: function(value) {
      var self = this;
      self.element.val(value);
      self._refreshClearIcon();
    },

    setIconsVisibility: function(visibility) {
      var self = this;
      self.clearIcon.css('visibility', visibility);
    },
  });
})(jQuery);
