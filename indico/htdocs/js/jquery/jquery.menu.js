/* This file is part of CDS Indico.
 * Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
 *
 * CDS Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * CDS Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

$(function() {

    $.widget( "ui.dropdown", {
        options: {
            effect_on: 'slideDown',
            effect_off: 'fadeOut',
            time_on: 200,
            time_off: 200,
            positioning: {}
        },

        _close: function(elem, effect) {
            this._effect('off', elem.siblings('ul'), effect);
            elem.siblings('ul').find('ul').hide();
            elem.data('on', false);
            elem.parent().removeClass('selected');
            elem.siblings('ul').find('a').data('on', false);
        },

        _close_all: function(effect) {
            var self = this;
            this.element.children().find('a').each(function() {
                self._close($(this), effect);
            });
        },

        _open: function(elem) {
            var self = this;
            var sibl = elem.siblings('ul');
            this._effect('on', sibl);
            elem.data('on', true);
            elem.parent().addClass('selected');
            sibl.position($.extend({of: elem.parent()}, this.options.positioning[sibl.data('level')] ||
                                   {my: 'left top', at: 'left bottom', offset: '0px 0px'}));
            elem.parent().siblings().find('a').each(function() {
                self._close($(this));
            });
        },

        _set_classes: function(elem, level) {
            var self = this;
            level = level || 0;
            elem.addClass('ui-list-menu-level-' + level);
            elem.addClass('ui-list-menu-level');
            elem.data('level', level);
            elem.children('li').children('ul').each(function() {
                self._set_classes($(this), level + 1);
            });
        },

        _menuize: function(elem) {
            var self = this;

            this._set_classes(elem);

            elem.addClass('ui-list-menu');
            elem.find('li a').each(function() {
                $this = $(this);
                if ($this.siblings('ul').length) {
                    $this.data('expandable', true);
                    $this.parent().addClass('arrow');
                }
                $this.siblings('ul').hide();
                $this.parent().addClass('');
            }).click(function() {
                var $this = $(this);
                if ($this.data('expandable')) {
                    if ($this.data('on')) {
                        self._close($this);
                    } else {
                        self._open($this);
                    }
                    return false;
                } else {
                    var result = $this.triggerHandler('menu_select', self.element);
                    if(!result) {
                        self._close_all();
                    }
                    return false;
                }
            });
        },

        _create: function() {
            var self = this;
            this._menuize(this.element);
            $('html').live('click', function() {
                self._close_all();
            });
        },

        _effect: function(st, elem, effect) {
            if (effect === undefined) {
                var func = this.options['effect_' + st];
            } else {
                var func = effect;
            }

            if (func === null) {
                // no pretty effects
                elem.hide();
            }
            else if (typeof func == 'function') {
                func.call(elem, this);
            } else {
                elem[func].call(elem, this.options['time_' + st]);
            }
        },

        close: function() {
            this._close_all(null);
        }
    });
});