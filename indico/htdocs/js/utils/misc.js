/* This file is part of Indico.
 * Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
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

(function(global) {
    'use strict';

    global.confirmPrompt = function confirmPrompt(message, title) {
        var dfd = $.Deferred();
        message = $('<div>', {width: 400, html: message});
        new ConfirmPopup(title || $T('Please confirm'), message, function(confirmed) {
            if (confirmed) {
                dfd.resolve();
            } else {
                dfd.reject();
            }
        }).open();
        return dfd.promise();
    }
})(window);
