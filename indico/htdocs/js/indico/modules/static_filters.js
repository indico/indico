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

(function(global) {
    'use strict';

    var totalDurationDisplay;

    function formatState(visible, total) {
        return '{0} / {1}'.format('<strong>{0}</strong>'.format(visible.length), total.length);
    }

    function setState(state, visible, total) {
        state.html($('<span>').append(formatState(visible, total)));
        state.attr('title', $T.gettext("{0} out of {1} displayed").format(visible.length, total.length));
        if (!totalDurationDisplay) {
            totalDurationDisplay = $('#total-duration').detach();
        }
    }

    function _applySearchFilters(searchBoxConfig) {
        var $items = $(searchBoxConfig.listItems);
        var term = $(searchBoxConfig.term).val().trim();
        var $state = $(searchBoxConfig.state);
        var $visibleEntries, m;
        var $filterPlaceholder = $(searchBoxConfig.placeholder);
        $filterPlaceholder.hide();
        $state.removeClass('active');

        if (!term) {
            $items.show();
            setState($state, $items, $items);
            if (totalDurationDisplay) {
                $state.after(totalDurationDisplay);
                totalDurationDisplay = null;
            }
            return;
        }

        // quick search of contribution by ID
        if ((m = term.match(/^#(\d+)$/))) {
            $visibleEntries = $items.filter('[data-friendly-id="' + m[1] + '"]');
        } else {
            $visibleEntries = $items.find('[data-searchable*="' + term.toLowerCase() + '"]')
                                            .closest(searchBoxConfig.itemHandle);
        }

        if ($visibleEntries.length === 0) {
            $filterPlaceholder.text($T.gettext('There are no entries that match your search criteria.')).show();
            $state.addClass('active');
        } else if ($visibleEntries.length !== $items.length) {
            $state.addClass('active');
        }

        setState($state, $visibleEntries, $items);

        $items.hide();
        $visibleEntries.show();

        // Needed because $(window).scroll() is not called when hiding elements
        // causing scrolling elements to be out of place.
        $(window).trigger('scroll');
    }

    global.setupSearchBox = function setupSearchBox(config) {
        var applySearchFilters = _.partial(_applySearchFilters, config);

        $(config.term).realtimefilter({
            callback: applySearchFilters
        });

        // make sure that filters are applied when e.g. going back in
        // browser history, this is needed since typewatch, which is used internally
        // by realtimefilter, calls applySearchFilter only when user is typing
        applySearchFilters();
        return applySearchFilters;
    };
})(window);
