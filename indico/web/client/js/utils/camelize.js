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

import _ from 'lodash';


function smartCamelCase(string) {
    return _.camelCase(string).replace(/Url/g, 'URL');
}


export default function camelizeKeys(obj) {
    if (!_.isPlainObject(obj) && !_.isArray(obj)) {
        return obj;
    }

    if (_.isArray(obj)) {
        return obj.map(camelizeKeys);
    }

    return Object.entries(obj).reduce((accum, [key, value]) => {
        if (key.match(/^[A-Za-z_]+$/)) {
            return {...accum, [smartCamelCase(key)]: camelizeKeys(value)};
        } else {
            return {...accum, [key]: camelizeKeys(value)};
        }
    }, {});
}
