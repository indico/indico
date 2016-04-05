(function(global) {
    'use strict';

    var searchBoxConfig;

    function formatState(visible, total) {
        return '{0} / {1}'.format('<strong>{0}</strong>'.format(visible.length), total.length);
    }

    function setState(state, visible, total) {
        state.html(formatState(visible, total));
        state.attr('title', $T.gettext("{0} out of {1} displayed").format(visible.length, total.length));
    }

    global.applySearchFilters = function applySearchFilters() {
        var $contributions = $(searchBoxConfig.listItems),
            term = $(searchBoxConfig.term).val().trim(),
            $state = $(searchBoxConfig.state),
            $visibleEntries,
            m,
            $filterPlaceholder = $(searchBoxConfig.placeholder);

        $filterPlaceholder.hide();
        $state.removeClass('active');

        if (!term) {
            $contributions.show();
            setState($state, $contributions, $contributions);
            return;
        }

        // quick search of contribution by ID
        if ((m = term.match(/^#(\d+)$/))) {
            $visibleEntries = $('[data-friendly-id="' + m[1] + '"]');
        } else {
            $visibleEntries = $contributions.find('[data-searchable*="' + term.toLowerCase() + '"]')
                                            .closest(searchBoxConfig.itemHandle);
        }

        if ($visibleEntries.length === 0) {
            $filterPlaceholder.text($T.gettext('There are no entries that match your search criteria.')).show();
            $state.addClass('active');
        } else if ($visibleEntries.length !== $contributions.length) {
            $state.addClass('active');
        }

        setState($state, $visibleEntries, $contributions);

        $contributions.hide();
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
