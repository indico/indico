(function(global) {
    'use strict';

    var searchBoxConfig, totalDurationDisplay;

    function formatState(visible, total) {
        return '{0} / {1}'.format('<strong>{0}</strong>'.format(visible.length), total.length);
    }

    function setState(state, visible, total) {
        state.html(formatState(visible, total));
        state.attr('title', $T.gettext("{0} out of {1} displayed").format(visible.length, total.length));
        if (!totalDurationDisplay) {
            totalDurationDisplay = $('#total-duration').detach();
        }
    }

    global.applySearchFilters = function applySearchFilters() {
        var $items = $(searchBoxConfig.listItems),
            term = $(searchBoxConfig.term).val().trim(),
            $state = $(searchBoxConfig.state),
            $visibleEntries,
            m,
            $filterPlaceholder = $(searchBoxConfig.placeholder);

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
    };

    global.setupSearchBox = function setupSearchBox(config) {
        searchBoxConfig = config;

        $('#search-input').realtimefilter({
            callback: applySearchFilters
        });
    };
})(window);
