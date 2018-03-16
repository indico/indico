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

import fetch from 'cross-fetch';

export const SET_KEYWORD = 'SET_KEYWORD';
export const SET_FILTER = 'SET_FILTER';
export const SET_PAGE = 'SET_PAGE';
export const UPDATE_ENTRIES = 'UPDATE_ENTRIES';
export const FETCH_STARTED = 'FETCH_STARTED';


export function setKeyword(keyword) {
    return { type: SET_KEYWORD, keyword };
}

export function setFilter(filter) {
    return { type: SET_FILTER, filter };
}

export function setPage(page) {
    return { type: SET_PAGE, page };
}

export function updateEntries(entries) {
    return { type: UPDATE_ENTRIES, entries };
}

export function fetchStarted() {
    return { type: FETCH_STARTED };
}

export function fetchPosts(url, page = null, pageSize = 10) {
    return dispatch => {
        dispatch(fetchStarted());

        const options = {
            method: 'GET',
            credentials: 'same-origin', // use cookies for authentication
        };

        return fetch(url, options)
            .then(data => data.json())
            .then(json => {
                dispatch(updateEntries(json.entries));
            });
    };
}
