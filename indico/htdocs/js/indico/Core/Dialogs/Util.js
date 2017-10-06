/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

    var ERROR_DIALOG_TEMPLATE = _.template(
        '<div class="error-dialog">' +
        '    <div class="error-message-box">' +
        '        <div class="message-text"><%= errorText %></div>' +
        '    </div>' +
        '    <p class="js-info-text"><%= infoText %></p>' +
        '    <div class="actions">' +
        '        <button class="i-button big warning js-report-button"' +
        '                data-href="<%= url %>"' +
        '                data-title="<%= reportText %>"' +
        '                data-ajax-dialog>' +
        '            <%= reportText %>' +
        '        </button>' +
        '        <button class="i-button big" data-button-back><%= closeText %></button>' +
        '    </div>' +
        '</div>'
    );

    global.showErrorDialog = function showErrorDialog(error) {
        var $content = $(ERROR_DIALOG_TEMPLATE({
            errorText: error.message,
            infoText: $T.gettext('Please reload the page and report this error to us if it persists.'),
            reportText: $T.gettext('Report Error'),
            closeText: $T.gettext('Close'),
            url: error.report_url
        }));
        $content.on('ajaxDialog:closed', function(evt, data) {
            if (data) {
                $content.find('.js-report-button').prop('disabled', true);
                $content.find('.js-info-text').text($T.gettext('Thanks for your error report!'));
            }
        });
        ajaxDialog({
            content: $content,
            title: error.title,
            onOpen: function() {
                if (!error.report_url) {
                    $content.find('.js-report-button').remove();
                    $content.find('.js-info-text').remove();
                }
            }
        });
    };

    IndicoUI.Dialogs.Util = {
        progress: function(text) {
            var dialog = new ProgressDialog(text);
            dialog.open();

            return function() {
                dialog.close();
            };
        }
    };
})(window);
