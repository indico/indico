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

/* eslint-disable import/no-commonjs, import/unambiguous */
/* global module:false __dirname:false */

const path = require('path');
const nodeResolve = require('eslint-import-resolver-node').resolve;


module.exports = {
    interfaceVersion: 2,
    resolve(source, file, config) {
        const rv = nodeResolve(source, file, config);
        if (rv.found) {
            return rv;
        } else if (source.startsWith('indico/')) {
            const realPath = path.join(__dirname, '../indico/web/client/js', source.substr(7));
            return nodeResolve(realPath, file, config);
        }
        return {found: false};
    }
};
