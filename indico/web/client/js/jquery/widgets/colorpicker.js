// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function($) {
  $.widget('indico.indicoColorpicker', {
    updateWidget: function() {
      this.$preview.toggleClass('no-value', !this.$colorInput.val().length);
      const val = this.$colorInput.val();
      if (!val) {
        this.$preview.attr('style', null);
      }
    },

    _create: function() {
      let oldValue;
      const $element = this.element;
      const $preview = (this.$preview = $element.find('.color-preview'));
      const $colorInput = (this.$colorInput = $element.find('input'));

      $colorInput.colorpicker({
        colorFormat: '#HEX',
        altField: $preview,
        open: () => {
          oldValue = $colorInput.val();
        },
        ok: () => {
          this.updateWidget();
        },
        select: () => {
          this.updateWidget();
        },
        cancel: () => {
          $colorInput.val(oldValue);
          this.updateWidget();
          $colorInput.trigger('cancel');
        },
      });

      this.updateWidget();
    },
  });
})(jQuery);
