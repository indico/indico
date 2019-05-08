// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global ChooseUsersPopup:false */

import impersonateURL from 'indico-url:auth.admin_impersonate';

import {indicoAxios, handleAxiosError} from 'indico/utils/axios';
import {$T} from 'indico/utils/i18n';


async function sendRequest(data) {
    try {
        await indicoAxios.post(impersonateURL(), data);
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
