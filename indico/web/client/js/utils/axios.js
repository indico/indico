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

/* global showErrorDialog:false */

import axios from 'axios';
import isURLSameOrigin from 'axios/lib/helpers/isURLSameOrigin';
import qs from 'qs';

import {$T} from 'indico/utils/i18n';


export const indicoAxios = axios.create({
    paramsSerializer: (params) => qs.stringify(params, {arrayFormat: 'repeat'}),
    xsrfCookieName: null,
    xsrfHeaderName: null,
});

indicoAxios.interceptors.request.use((config) => {
    if (isURLSameOrigin(config.url)) {
        config.headers.common['X-Requested-With'] = 'XMLHttpRequest';  // needed for `request.is_xhr`
        config.headers.common['X-CSRF-Token'] = document.getElementById('csrf-token').getAttribute('content');
    }
    return config;
});


export function handleAxiosError(error) {
    if (error.response && error.response.data && error.response.data.error) {
        showErrorDialog(error.response.data.error);
    } else {
        showErrorDialog({
            title: $T.gettext('Something went wrong'),
            message: error.message,
            suggest_login: false,
            report_url: null
        });
    }
}

export default indicoAxios;
