// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

IndicoUI.Widgets = {
  /**
        @namespace Generic, resusable, components
        */
  Generic: {
    /**
     * (DEPRECATED)
     * Creates a tooltip above the given element.
     * Example of usage:
     *
     * var homeButtonPopup = function(event) {
     *     IndicoUI.Widgets.Generic.tooltip(this, event, "<span style='padding:3px'>Go to Indico Home Page</span>");
     * }
     * $E('homeButton').dom.onmouseover = homeButtonPopup;
     *
     * @param {Object} in_this (view example)
     * @param {Object} event (view example)
     * @param {String} content Whatever content is desired.
     */
    tooltip: function(in_this, event, content) {
      var $this = $(in_this);
      if ($this.data('hasTooltip')) {
        return;
      }
      $this.data('hasTooltip', true).qtip({
        content: {
          text: content,
        },
        show: {
          ready: true,
        },
      });

      // Return the onmouseout handler in case
      // it needs to be called from outside
      return function() {
        $this.qtip('hide');
      };
    },
  },
};
