// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function($) {
  'use strict';

  $.widget('indico.actioninput', $.indico.clearableinput, {
    options: {
      actionCallback: function() {},
      actionIcon: 'icon-checkmark',
      alwaysClearable: true,
      enterKeyEnabled: true,
    },

    _create: function() {
      var self = this;
      var input = self.element;

      self._super();

      self.actionIcon = $(
        '<a class="i-link accept hide-if-locked {0}"></a>'.format(self.options.actionIcon)
      )
        .css('line-height', input.css('height'))
        .click(function() {
          self._action();
        });

      input.on('keydown keypress', function(e) {
        if (e.key === 'Enter' && self.options.enterKeyEnabled) {
          self._action();
        }
      });

      self.buttonBox.prepend(self.actionIcon);
      input.addClass('actionabletext');
    },

    _action: function() {
      var self = this;
      var opt = self.options;
      var input = self.element;

      opt.actionCallback();

      if (opt.focusOnClear) {
        input.focus();
      } else {
        input.blur();
      }
    },

    initSize: function(fontSize, lineHeight) {
      var self = this;

      self._super(fontSize, lineHeight);
      self.actionIcon.css('font-size', self.size.fontSize);
      self.actionIcon.css('line-height', self.size.lineHeight);
    },

    setIconsVisibility: function(visibility) {
      var self = this;

      self._super(visibility);
      self.actionIcon.css('visibility', visibility);
    },
  });
})(jQuery);
