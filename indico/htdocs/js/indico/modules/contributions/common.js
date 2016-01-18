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

    function formatState(visible, total) {
        return $T.gettext('{0} / {1}').format('<strong>{0}</strong>'.format(visible.length),
                                              total.length);
    }

    function setState(visible, total) {
        var $state = $('#filtering-state'),
            title = '{0} out of {1} contributions displayed'.format(visible.length, total.length);
        $state.html(formatState(visible, total));

        // oldtitle needs to be updated too, because of qTip
        $state.attr({
            oldtitle: title,
            title: title
        });
    }

    function applyFilters() {
        var contributions = $('#contribution-list tbody tr'),
            term = $('#search-input').val().trim(),
            visibleEntries, m,
            $state = $('#filtering-state'),
            $filterPlaceholder = $('#filter-placeholder');

        $filterPlaceholder.hide();
        $state.removeClass('active');

        if (!term) {
            contributions.show();
            setState(contributions, contributions);
            return;
        }

        // quick search of contribution by ID
        if (m = term.match(/^#(\d+)$/)) {
            visibleEntries = $('#contrib-' + m[1]);
        } else {
            visibleEntries = contributions.find('td[data-searchable*="' + term + '"]').closest('tr');
        }

        if (visibleEntries.length === 0) {
            $filterPlaceholder.text($T.gettext('There are no contributions that match your search criteria.')).show();
            $state.addClass('active');
        } else if (visibleEntries.length !== contributions.length) {
            $state.addClass('active');
        }

        setState(visibleEntries, contributions);

        contributions.hide();
        visibleEntries.show();

        // Needed because $(window).scroll() is not called when hiding elements
        // causing scrolling elements to be out of place.
        $(window).trigger('scroll');
    }

    function setupSearchBox() {
        $('#search-input').realtimefilter({
            callback: function() {
                applyFilters();
            }
        });
    }

    global.setupContributionList = function setupContributionList() {
        setupTableSorter();
        setupSearchBox();
        enableIfChecked('#contribution-list', 'input[name=contribution_id]', '.js-enable-if-checked');
        $('#contribution-list').on('indico:htmlUpdated', function() {
            setupTableSorter();
            applyFilters();
        });
    };
})(window);
