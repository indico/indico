// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* eslint-disable import/unambiguous */

(function($) {
  $.widget('indico.palettepicker', {
    options: {
      availableColors: [],
      onSelect: null,
      numColumns: 5,
      selectedColor: null,
      qtipConstructor: null,
    },

    _create() {
      const self = this;
      const element = this.element;
      const paletteTable = $('<table>', {class: 'palette-picker'});
      const availableColors = this.options.availableColors;
      let tr = this._createTableRow();

      self._paletteTable = paletteTable;

      $.each(availableColors, (index, color) => {
        const td = $('<td>', {
          class: 'palette-color',
          data: {color},
        });

        const colorBox = $('<div>', {
          css: {background: `#${color.background}`},
          class: 'background-box',
        });

        colorBox.append(
          $('<div>', {
            css: {background: `#${color.text}`},
            class: 'text-box',
          })
        );

        td.append(colorBox);
        tr.append(td);

        if ((index + 1) % self.options.numColumns === 0) {
          paletteTable.append(tr);
          tr = self._createTableRow();
        }
      });

      if (tr.children().length) {
        paletteTable.append(tr);
      }

      paletteTable.on('click', '.palette-color', function() {
        const $this = $(this);
        const color = $this.data('color');
        const backgroundColor = `#${color.background}`;
        const textColor = `#${color.text}`;
        const styleObject = element[0].style;

        self.options.selectedColor = color;
        self._updateSelection();

        styleObject.setProperty('color', textColor, 'important');
        styleObject.setProperty('background', backgroundColor, 'important');

        if (self.options.onSelect) {
          self.options.onSelect.call(element, backgroundColor, textColor);
        }

        element.qtip('hide');
      });

      const qtipOptions = {
        prerender: false,
        overwrite: false,
        suppress: false,
        style: {
          classes: 'palette-picker-qtip',
        },
        position: {
          my: 'top center',
          at: 'bottom center',
          target: element,
          adjust: {
            mouse: false,
            scroll: false,
          },
        },
        content: {
          text: paletteTable,
        },
        show: {
          event: 'click',
          solo: true,
        },
        hide: {
          event: 'unfocus',
        },
        events: {
          show: self._updateSelection.bind(self),
        },
      };
      if (self.options.qtipConstructor) {
        self.options.qtipConstructor(element, qtipOptions);
      } else {
        element.qtip(qtipOptions);
      }
    },

    _createTableRow() {
      return $('<tr>', {height: 13});
    },

    _updateSelection() {
      const selectedColor = this.options.selectedColor;
      this._paletteTable.find('.palette-color').each(function() {
        const $this = $(this);
        const color = $this.data('color');
        if (
          selectedColor !== null &&
          color.background === selectedColor.background &&
          color.text === selectedColor.text
        ) {
          $this.addClass('selected');
        } else {
          $this.removeClass('selected');
        }
      });
    },
  });
})(jQuery);
