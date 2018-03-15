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

import Jed from 'jed';
import _ from 'underscore';

export const defaultI18n = new Jed({
    locale_data: global.TRANSLATIONS,
    domain: "indico"
});

export const $T = _.bind(defaultI18n.gettext, defaultI18n);

['gettext', 'ngettext', 'pgettext', 'npgettext', 'translate'].forEach(function(name) {
    $T[name] = _.bind(defaultI18n[name], defaultI18n);
});

$T.domain = _.memoize(function(domain) {
    return new Jed({
        locale_data: global.TRANSLATIONS,
        domain: domain
    });
});
