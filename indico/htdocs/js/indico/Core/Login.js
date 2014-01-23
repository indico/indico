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

function loginAs() {
    var popup = new ChooseUsersPopup(
        $T("Select user to log in as"), true, null, false,
        true, true, true, true, false,
        function(user) {
            indicoRequest(
                'admin.header.loginAs',
                {
                    userId: user[0]['id']
                },
                function(result, error) {
                    if (!error) {
                        // redirect to the same page
                        window.location.reload();
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
            );
        });
    popup.execute();
}

function undoLoginAs() {
    indicoRequest('admin.header.undoLoginAs', {}, function(result, error) {
        if (!error) {
            window.location.reload();
        }
        else {
            IndicoUtil.errorReport(error);
        }
    });
}

$(document).ready(function() {
    $('.login-as').on('click', function(e) {
        e.preventDefault();
        loginAs();
    });


    $('.undo-login-as').on('click', function(e) {
        e.preventDefault();
        undoLoginAs();
    });
});
