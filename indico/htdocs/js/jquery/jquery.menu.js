/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

(function($) {

    $.widget('ui.dropdown', {
        options: {
            effect_on: 'slideDown',
            effect_off: 'fadeOut',
            time_on: 200,
            time_off: 200,
            positioning: {}
        },

        _close: function(elem, effect) {
            var ul = elem.next('ul');

            elem.removeClass('open');

            this._effect('off', ul, effect);
            ul.find('ul').hide();
            elem.data('on', false);
            elem.parent().removeClass('selected');
            elem.siblings('ul').find('a').data('on', false);
        },

        _close_all: function(effect) {
            var self = this;

            this.element.find('a').each(function() {
                self._close($(this), effect);
            });
        },

        _open: function(elem) {
            var self = this;
            var sibl = elem.next('ul.dropdown');

            elem.addClass('open');

            this._effect('on', sibl);
            elem.data('on', true);
            elem.parent().addClass('selected');
            sibl.position($.extend({of: elem}, this.options.positioning[sibl.data('level')] ||
                                   {my: 'left top', at: 'left bottom', offset: '0px 0px'}));
            this.element.find('a').each(function() {
                if (this != elem.get(0)) {
                    self._close($(this));
                }
            });
        },

        _menuize: function(elem) {
            var self = this;

            elem.find('.i-button').each(function() {
                var $this = $(this);
                if (!$this.attr('href') || $this.attr('href') == "#") {
                    $this.click(function(e) {
                        if ($this.data('toggle') == 'dropdown') {
                            if ($this.data('on')) {
                                self._close($this);
                            } else {
                                self._open($this);
                            }
                            e.preventDefault();
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

            elem.find('ul.dropdown > li > a').each(function() {
                var $this = $(this);
                if (!$this.attr('href') || $this.attr('href') == "#") {
                    $this.click(function(e) {
                        var result = $this.triggerHandler('menu_select', self.element);
                        if(!result) {
                            self._close_all();
                        }
                        e.preventDefault();
                    });
                }
            });

            elem.find('ul.dropdown > li.toggle').each(function() {
                var li = $(this);
                var link = $('<a>', {
                    'href': '#',
                    'text': li.text(),
                    'class': 'icon-checkmark ' + (li.data('state') ? '' : 'inactive'),
                    'click': function(e) {
                        e.preventDefault();
                        var $this = $(this);
                        var newState = !li.data('state');
                        $this.toggleClass('inactive', !newState);
                        li.data('state', newState);
                        li.triggerHandler('menu_toggle', [newState]);
                    }
                });
                li.html(link);
            });
        },

        _create: function() {
            var self = this;
            this._menuize(this.element);
            $(document).on('click', function(e){
                // click outside? close menus.
                if ($(self.element).has(e.target).length == 0) {
                    self._close_all();
                }
            });
        },

        _effect: function(st, elem, effect) {
            var func = effect === undefined ? this.options['effect_' + st] : effect;

            if (func === null) {
                // no pretty effects
                elem.hide();
            }
            else if (typeof func == 'function') {
                func.call(elem, this);
            }
            else {
                elem[func].call(elem, this.options['time_' + st]);
            }
        },

        close: function() {
            this._close_all(null);
        }
    });
})(jQuery);
