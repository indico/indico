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

/* global ChooseUsersPopup:false */

(function() {
    'use strict';

    function sendRequest(url, payload) {
        $.ajax({
            url: url,
            method: 'POST',
            data: payload,
            complete: IndicoUI.Dialogs.Util.progress(),
            error: handleAjaxError,
            success: function() {
                IndicoUI.Dialogs.Util.progress();
                location.reload();
            }
        });
    }

    function impersonateUser(url) {
        function _userSelected(users) {
            sendRequest(url, {user_id: users[0].id});
        }

        var dialog = new ChooseUsersPopup(
            $T("Select user to impersonate"),
            true, null, false, true, null, true, true, false, _userSelected, null, false
        );

        dialog.execute();
    }

    function undoImpersonateUser(url) {
        sendRequest(url, {undo: '1'});
    }

    $(document).ready(function() {
        $('.login-as').on('click', function(evt) {
            evt.preventDefault();
            impersonateUser($(this).data('href'));
        });

        $('.undo-login-as').on('click', function(evt) {
            evt.preventDefault();
            undoImpersonateUser($(this).data('href'));
        });
    });
})();
