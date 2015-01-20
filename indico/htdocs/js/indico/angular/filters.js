/* This file is part of Indico.
 * Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
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

var ndFilters = angular.module("ndFilters", []);

ndFilters.filter("i18n", function() {
    return function(input) {
        return $T(input);
    };
});

ndFilters.filter("range", function() {
    return function(input, min, max) {
        min = parseInt(min, 10) || 0;
        max = parseInt(max, 10);
        for (var i=min; i<=max; i++) {
            input.push(i);
        }
        return input;
    };
});
