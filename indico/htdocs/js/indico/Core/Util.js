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


/**
 * Truncates a category path if it is too long.
 */
Util.truncateCategPath = function(list) {
    var first = list.slice(0,1);
    var last = list.length>1?list.slice(-1):[];
    list = list.slice(1,-1);

    var truncated = false;

    var chars = list.join('');
    while(chars.length > 10) {
        truncated = true;
        list = list.slice(1);
        chars = list.join('');
    }

    if (truncated) {
        list = concat(['...'], list);
    }

    return translate(concat(first,list,last),
               function(val) {
                   return escapeHTML(val);
               });
};
