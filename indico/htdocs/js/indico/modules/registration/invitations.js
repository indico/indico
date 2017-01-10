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

    global.setupInvitationPage = function setupInvitationPage() {
        $('#invitation-list').on('indico:confirmed', '.js-invitation-action', function(evt) {
            evt.preventDefault();

            var $this = $(this);
            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function(data) {
                    $('#invitation-list').html(data.invitation_list);
                }
            });
        });

        $('.js-invite-user').ajaxDialog({
            onClose: function(data) {
                if (data) {
                    $('#invitation-list').html(data.invitation_list);
                }
            }
        });
    };
})(window);
