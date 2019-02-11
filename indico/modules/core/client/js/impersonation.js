/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import getImpersonateURL from 'indico-url:auth.admin_impersonate';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {$T} from 'indico/utils/i18n';


async function sendRequest(data) {
    try {
        await indicoAxios.post(getImpersonateURL(), data);
    } catch (error) {
        handleAxiosError(error);
        return;
    }
    window.location.reload();
}

function impersonateUser() {
    function _userSelected(users) {
        sendRequest({user_id: users[0].id});
    }

    const dialog = new ChooseUsersPopup(
        $T('Select user to impersonate'),
        true, null, false, true, null, true, true, false, _userSelected, null, false
    );

    dialog.execute();
}

document.addEventListener('DOMContentLoaded', () => {
    const undoLoginAs = document.querySelectorAll('.undo-login-as');
    const loginAs = document.querySelector('#login-as');

    if (undoLoginAs.length) {
        undoLoginAs.forEach(elem => {
            elem.addEventListener('click', e => {
                e.preventDefault();
                sendRequest({undo: true});
            });
        });
    }
    if (loginAs) {
        loginAs.addEventListener('click', e => {
            e.preventDefault();
            impersonateUser();
        });
    }
});
