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

(function($) {
    'use strict';

    /*
     * This provides an untility for checkboxes (usually switch widgets) which immediately
     * save the state using an AJAX request. The checkbox is disabled during the AJAX request
     * to avoid the user from clicking multiple times and spamming unnecessary AJAX requests.
     *
     * The following data attributes may be set on the checkbox to configure the behavior:
     * - href: required, URL for the AJAX request
     * - confirm_enable: optional, show confirmation prompt when checking the checkbox if set
     * - confirm_disable: optional, show confirmation prompt when unchecking the checkbox if set
     */
    $.fn.ajaxCheckbox = function ajaxCheckbox() {
        return this.on('click', function(e) {
            e.preventDefault();
            var $this = $(this);
            var checked = this.checked;
            var message = checked ? $this.data('confirm_enable') : $this.data('confirm_disable');
            var deferred = message ? confirmPrompt(message) : $.Deferred().resolve();
            deferred.then(function() {
                // update check state and prevent changes until the request finished
                $this.prop('checked', checked).prop('disabled', true);
                $.ajax({
                    url: $this.data('href'),
                    method: 'POST',
                    dataType: 'json',
                    data: {
                        enabled: checked ? '1' : '0'
                    },
                    complete: function() {
                        $this.prop('disabled', false);
                    },
                    error: function(data) {
                        handleAjaxError(data);
                        $this.prop('checked', !checked);
                    },
                    success: function(data) {
                        $this.prop('checked', data.enabled);
                        if (data.flashed_messages) {
                            var flashed = $(data.flashed_messages.trim()).children();
                            if (flashed.length) {
                                $('#flashed-messages').empty().append(flashed);
                            }
                        }
                    }
                });
            });
        });
    };
})(jQuery);
