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

import './compat/jquery-ui';
import './contrib/jquery-extra-selectors';

import 'jquery-colorbox';
import 'jquery-colorbox/example1/colorbox.css';

import 'jquery-form';
import 'jstorage';

// moment.js locales
import 'moment/locale/en-gb';
import 'moment/locale/fr';
import 'moment/locale/es';

import 'tablesorter';
import Taggle from 'taggle';

import 'qtip2';
import 'qtip2/dist/jquery.qtip.css';

import 'vanderlee-colorpicker';
import 'vanderlee-colorpicker/jquery.colorpicker.css';

import './widgets';

// i18n (Jed)
import {defaultI18n, $T} from '../utils/i18n';

// Constructs that extend the behaviour
// of the HTML
import './extensions/clipboard';
import './extensions/global';

// Utility global functions
import './utils/ajaxdialog';
import './utils/ajaxform';
import './utils/declarative';
import './utils/defaults';
import './utils/dropzone';
import './utils/errors';
import './utils/forms';
import './utils/misc';
import './utils/routing';
import './utils/sortablelist';


// jQuery-migrate should be muted when in production
if (process.env.NODE_ENV !== 'development') {
    $.migrateMute = true;
}
// explicit tracebacks are not needed
$.migrateTrace = false;
require('jquery-migrate');

// These global definitions are needed so that
// legacy code can access them globally
Object.assign(window, {
    _, moment, $T,
    i18n: defaultI18n
});

window.Taggle = Taggle;
