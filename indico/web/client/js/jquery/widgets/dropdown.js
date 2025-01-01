// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

(function($) {
  $.widget('indico.dropdown', {
    options: {
      selector: '.i-button[data-toggle]',
      effect_on: 'slideDown',
      effect_off: 'fadeOut',
      time_on: 200,
      time_off: 200,
      positioning: {},
      relative_to: undefined,
      always_listen: false, // if set to true, will trigger 'menu_select' event even when there is a valid href
    },

    _close: function(elem, effect) {
      var ul = elem.next('ul');

      elem.removeClass('open');
      elem.removeData('no-qtip');

      this._effect('off', ul, effect);
      ul.find('ul').hide();
      elem.data('on', false);
      elem.parent().removeClass('selected');
      elem
        .siblings('ul')
        .find('a')
        .data('on', false);
    },

    _close_all: function(effect) {
      var self = this;

      this.element.find('a, button').each(function() {
        self._close($(this), effect);
      });
    },

    _open: function(elem) {
      var self = this;
      var sibl = elem.next('ul.i-dropdown');
      var positionReference = this.options.relative_to || elem;

      elem.addClass('open');
      elem.data('no-qtip', true).trigger('indico:closeAutoTooltip');

      this._effect('on', sibl);
      elem.data('on', true);
      elem.parent().addClass('selected');
      sibl.position(
        $.extend(
          {of: positionReference},
          this.options.positioning[sibl.data('level')] || {
            my: 'left top',
            at: 'left bottom',
            offset: '0px 0px',
          }
        )
      );
      this.element.find('a').each(function() {
        if (this !== elem.get(0)) {
          self._close($(this));
        }
      });
    },

    _menuize: function(elem) {
      var self = this;

      elem.find(this.options.selector).each(function() {
        var $this = $(this);
        if (
          !$this.attr('href') ||
          $this.attr('href') === '#' ||
          $this.data('ignore-href') !== undefined ||
          self.options.always_listen
        ) {
          $this.on('click', function(e) {
            if ($this.data('toggle') === 'dropdown') {
              if ($this.data('on')) {
                self._close($this);
              } else if (!$this.hasClass('disabled')) {
                self._open($this);
              }
              e.preventDefault();
              e.stopPropagation();
            } else {
              var result = $this.triggerHandler('menu_select', self.element);
              if (!result) {
                self._close_all();
              }
              e.preventDefault();
            }
          });
        }
      });

      elem.find('ul.i-dropdown > li > a').each(function() {
        var $this = $(this);
        if (
          !$this.attr('href') ||
          $this.attr('href') === '#' ||
          $this.data('ignore-href') !== undefined ||
          self.options.always_listen
        ) {
          $this.on('click', function(e) {
            e.preventDefault();
            if ($this.hasClass('disabled')) {
              return;
            }
            var result = $this.triggerHandler('menu_select', self.element);
            if (!result) {
              self._close_all();
            }
          });
        }
      });

      elem.find('ul.i-dropdown > li.toggle').each(function() {
        var li = $(this);
        var link = $('<a>', {
          href: '#',
          text: li.text(),
          class: 'icon-checkmark ' + (li.data('state') ? '' : 'inactive'),
          click: function(e) {
            e.preventDefault();
            var $this = $(this);
            var newState = !li.data('state');
            $this.toggleClass('inactive', !newState);
            li.data('state', newState);
            li.triggerHandler('menu_toggle', [newState]);
          },
        });
        li.html(link);
      });
    },

    _create: function() {
      var self = this;
      this._menuize(this.element);
      $(document).on('click', function(e) {
        // click outside? close menus.
        if ($(self.element).has(e.target).length === 0) {
          self._close_all();
        }
      });
    },

    _effect: function(st, elem, effect) {
      var func = effect === undefined ? this.options['effect_' + st] : effect;

      if (func === null) {
        // no pretty effects
        elem.hide();
      } else if (typeof func == 'function') {
        func.call(elem, this);
      } else {
        elem[func].call(elem, this.options['time_' + st]);
      }
    },

    close: function() {
      this._close_all(null);
    },
  });
})(jQuery);
