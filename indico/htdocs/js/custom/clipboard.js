/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

$(document).ready(function() {
    'use strict';

    /* Show a qTip with the given text under the given element. The qTip is
     * destroyed when hidden and thus will be shown only once. */
    function showQTip(element, text, hideAfterDelay) {
        var container = $('<span>').qtip({
            overwrite: true,
            position: {
                target: $(element)
            },
            content: {
                text: text
            },
            show: {
                solo: true
            },
            hide: {
                event: 'unfocus click'
            },
            events: {
                hide: function(evt, api) {
                    $(this).qtip('destroy');
                }
            }
        });
        container.qtip('show');

        if (hideAfterDelay) {
            setTimeout(function() {
                container.qtip('hide')
            }, 3000);
        }
    }

    /* Handle clicks on .js-copy-to-clipboard with cliboard.js.
     * For simple usage, the clipboard-text data attribute will be copied to
     * the system clipboard. For other possibilities, see https://clipboardjs.com/
     * */
    var c = new Clipboard('.js-copy-to-clipboard');
    c.on('success', function(evt) {
        showQTip(evt.trigger, $T.gettext("Copied to clipboard"), true);
    });
    c.on('error', function(evt) {
        var copyShortcut = "CTRL-C";
        if (/^Mac/i.test(navigator.platform)) {
            copyShortcut = "⌘-C";
        }
        copyShortcut = "<strong>" + copyShortcut + "</strong>";
        showQTip(evt.trigger, $T.gettext("Press {0} to copy").format(copyShortcut));
    });

    /* Allow to use clipboard.js on <a> with href attributes. */
    $('.js-copy-to-clipboard').on('click', function(evt) {
        evt.preventDefault();
    });
});
