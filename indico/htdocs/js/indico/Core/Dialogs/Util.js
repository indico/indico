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

IndicoUI.Dialogs.Util = {

    error: function(err) {
        var dialog = null;
        if (exists(err.type) && err.type === "noReport") {
            dialog = new NoReportErrorDialog(err);
        } else {
            dialog = new ErrorReportDialog(err);
        }
        dialog.open();
    },

    progress: function(text) {
        var dialog = new ProgressDialog(text);
        dialog.open();

        return function() {
            dialog.close();
        };
    },

    ttStatusInfo: function(text) {
        var stext = $('<div class="text"></div>').text(text ? $T(text) : null);
        var image = $('<img/>', {
            src: Indico.Urls.Base + "/images/loading.gif",
            alt: $T('Loading...')
        });

        var progress = $('<div id="tt_status_info"></div>').
            append(image, stext);

        $('#tt_status_info').replaceWith(progress).show();
        progress.fadeIn();

        return function() {
            progress.hide();
        };
    },

    alert: function(title, message) {
        var popup = new AlertPopup(title, message);
        popup.open();
    },

    confirm: function(title, message, handler) {
        var popup = new ConfirmPopup(title, message, handler);
        popup.open();
    }
};
