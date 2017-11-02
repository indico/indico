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

const global = window;

// moment.js locales
import 'moment/locale/en-gb.js';
import 'moment/locale/fr.js';
import 'moment/locale/es.js';

require('jquery-migrate');

// i18n (Jed)
import {defaultI18n, $T} from '../utils/i18n';

// These global definitions are needed until everything is on webpack
Object.assign(global, {
    $, jQuery, _, moment, $T,

    i18n: defaultI18n
});

import './modules/categories';
