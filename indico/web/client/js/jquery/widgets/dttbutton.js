// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */

/*
 * This widget extends an *existing* UI button to allow it to be disabled
 * and show a a tooltip while it is disabled.
 */
(function($) {
  $.widget(
    'indico.disabledButtonWithTooltip',
    $.extend({}, $.indico.disabledElementWithTooltip, {
      // Default options
      options: {
        elementClass: 'ui-dttbutton',
      },

      _create(...args) {
        this.isUIButton = this.element.is('.ui-button');
        if (this.options.disabled === null) {
          this.options.disabled = this.isUIButton
            ? this.element.button('option', 'disabled')
            : false;
        }
        $.indico.disabledElementWithTooltip.prototype._create.apply(this, args);
      },

      _update() {
        if (this.isUIButton) {
          this.element.button(!this.options.disabled ? 'enable' : 'disable');
        } else {
          this.element.prop('disabled', this.options.disabled);
        }
        this.overlay.toggle(this.options.disabled);
      },

      destroy(...args) {
        $.indico.disabledElementWithTooltip.prototype.destroy.apply(this, args);
        // restore ui-state-disabled since super's destroy removed it
        if (this.isUIButton) {
          this.element.button('option', 'disabled', this.options.disabled);
        }
      },

      _setOption(key, value) {
        if (key === 'disabled') {
          this.options.disabled = value;
          if (this.isUIButton) {
            // HACK HACK HACK: We only want the UI disabled class if it's an UI button.
            // Unfortunately there is no option to control this so we only call the super method
            // if we have an UI button.
            $.Widget.prototype._setOption.call(this, key, value);
          }
          this._update();
        } else {
          $.Widget.prototype._setOption.call(this, key, value);
        }
      },
    })
  );
})(jQuery);
