/* This file is part of Indico.
 * Copyright (C) 2002 - 2019 European Organization for Nuclear Research (CERN).
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

function number(value) {
    if (typeof value === 'number') {
        return value;
    } else if (typeof value === 'string') {
        if (value === '') {
            return null;
        } else if (!isNaN(+value)) {
            return +value;
        }
    }
    // keep whatever we have, maybe a validator can make sense of it
    // and show a suitable error
    return value;
}

function nullIfEmpty(value) {
    return value === '' ? null : value;
}


export default {
    number,
    nullIfEmpty,
};
