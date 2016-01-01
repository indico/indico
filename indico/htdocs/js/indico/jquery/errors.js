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

(function(global) {
    'use strict';

    global.handleAjaxError = function handleAjaxError(data) {
        if (data.responseText) {
            // $.ajax error callback, so data is the xhr object
            try {
                data = JSON.parse(data.responseText);
            } catch(e) {
                IndicoUI.Dialogs.Util.error({
                    code: data.status,
                    type: 'unknown',
                    message: data.statusText.toLowerCase(),
                    data: {},
                    inner: null,
                    requestInfo: {
                        url: data._requestURL  // set in beforeSend callback
                    }
                });
                return true;
            }
        }
        // data.data.error is only needed for angular error handlers
        var error = data.error || (data.data && data.data.error);
        if (error) {
            IndicoUI.Dialogs.Util.error(error);
            return true;
        }
    };

    // Select the field of an i-form which has an error and display the tooltip.
    global.showFormErrors = function showFormErrors(context) {
        context = context || $('body');
        context.find(".i-form .has-error > .form-field, .i-form .has-error > .form-subfield").each(function() {
            var $this = $(this);
            // Try a custom tooltip anchor
            var input = $this.find('[data-tooltip-anchor]');

            if (!input.length) {
                // Try the first non-hidden input field
                input = $this.children(':input:not(:hidden)').eq(0);
            }

            if (!input.length) {
                // Try the first element that's not a hidden input
                input = $this.children(':not(:input:hidden)').eq(0);
            }
            input.stickyTooltip('error', function() {
                return $this.data('error');
            });
        });
    };
})(window);
