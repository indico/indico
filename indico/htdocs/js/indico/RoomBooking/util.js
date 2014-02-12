/* This file is part of Indico.
 * Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
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

function is_date_valid(v) {
    if (!v)
        return false;

    // Checks for dd/mm/yyyy format.
    var dt = v.match(/^(\d{1,2})(\/|-)(\d{1,2})(\/|-)(\d{4})$/);
    if (dt == null) return false;

    day = dt[1];
    month = dt[3];
    year = dt[5];

    if (year < 1900 || year > 2100)
        return false;
    else if (month < 1 || month > 12)
        return false;
    else if (day < 1 || day > 31)
        return false;
    else if ([4, 6, 9, 11].indexOf(month) != -1 && day == 31)
        return false;
    else if (month == 2) {
        var isleap = (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0));
        if (day > 29 || (day == 29 && !isleap))
            return false;
    }
    return true;
}


function is_time_valid(v) {
    if (!v) return false;

    var t = v.match(/^(\d{1,2})-(\d{1,2})$/);
    if (t == null) return false;

    hour = t[1]
    min = [2]

    return hour >= 0 && hour <= 23 && min >= 0 && min <= 59
}

function is_datetime_valid(v) {
    if(!v) return false;

    var dt = v.split(/\s+/)
    if (!dt || a.length != 2) return false;
    return is_date_valid(dt[0]) && is_time_valid(dt[1])
}
