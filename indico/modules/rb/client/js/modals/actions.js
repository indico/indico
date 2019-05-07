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

import {push} from 'connected-react-router';
import qs from 'qs';

import {history} from '../store';

/**
 * Open a history-friendly modal, by setting the corresponding query string.
 *
 * @param {String} name - the name of the modal (e.g. 'room-details')
 * @param {String} value - a value to pass (normally an ID, e.g. room ID)
 * @param {Object} payload - additional information to pass as JSON
 * @param {Boolean} resetHistory - whether to erase any previous 'modal' path segments
 */
export function openModal(name, value = null, payload = null, resetHistory = false, overridePath = null) {
    let data = name;
    if (value !== null) {
        data += `:${value}`;
        if (payload !== null) {
            data += `:${JSON.stringify(payload)}`;
        }
    }

    const {location: {pathname: path, search: queryString}} = history;
    const qsData = queryString ? qs.parse(queryString.slice(1)) : {};
    if (resetHistory || !qsData.modal) {
        // if resetHistory was set, erase other 'modal' path segments
        qsData.modal = [];
    } else if (typeof qsData.modal === 'string') {
        qsData.modal = [qsData.modal];
    }
    qsData.modal.push(data);

    const serializedQs = qs.stringify(qsData, {allowDots: true, arrayFormat: 'repeat'});
    return push((overridePath || path) + (qsData ? `?${serializedQs}` : ''));
}
