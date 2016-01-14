/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

(function(global) {
    'use strict';

    function setupTableSorter() {
        $('#contribution-list .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            cssInfoBlock: 'avoid-sort',
            headerTemplate: '',
            sortList: [[1, 0]]
        });
    }

    global.setupContributionList = function setupContributionList() {
        setupTableSorter();
        enableIfChecked('#contribution-list', 'input[name=contribution_id]', '.js-enable-if-checked');
        $('#contribution-list').on('indico:htmlUpdated', function() {
            setupTableSorter();
        });
    };
})(window);
