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

// Indico-specific settings
$.extend(true, $.indico.daterange.prototype.options, {
    pickerOptions: { dateFormat: 'dd/mm/yy' },
    labelAttrs: { 'class': 'label titleCellFormat' },
    labels: [$T('Choose the start date'), $T('Choose the end date')]
});

$.fn.qtip.defaults = $.extend(true, {}, $.fn.qtip.defaults, {
    position: { my: 'top left', at: 'bottom right', viewport: $(window) },
    style: {tip: {corner: true}}
});

$.extend($.colorbox.settings, {
    opacity: 0.6
});

