(function(global) {
    'use strict';

    var searchBoxConfig;

    global.setupEventPersonsList = function setupEventPersonsList() {
        enableIfChecked('#persons-list', '.select-row:visible', '#persons-list .js-requires-selected-row');
        $('#persons-list [data-toggle=dropdown]').closest('.group').dropdown();

        $('#persons-list [data-filter]').on('click', function() {
            var personRows = $('#persons-list tr[data-person-roles]');
            var filters = $('#persons-list [data-filter]:checked').map(function() {
                return $(this).data('filter');
            }).get();

            var visibleEntries = personRows.filter(function() {
                var $this = $(this);

                return _.any(filters, function(filterName) {
                    return $this.data('person-roles')[filterName];
                });
            });

            personRows.hide();
            visibleEntries.show();
            $('#persons-list').trigger('indico:syncEnableIfChecked');
        });

        $('#persons-list td').on('mouseenter', function() {
            var $this = $(this);
            if (this.offsetWidth < this.scrollWidth && !$this.attr('title')) {
                $this.attr('title', $this.text());
            }
        });

        $('#persons-list .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            headerTemplate: '',
            sortList: [[1, 0]]
        });
    };

    function formatState(visible, total) {
        return '{0} / {1}'.format('<strong>{0}</strong>'.format(visible.length), total.length);
    }

    function setState(state, visible, total) {
        state.html(formatState(visible, total));
        state.attr('title', $T.gettext("{0} out of {1} displayed").format(visible.length, total.length));
    }

    global.applySearchFilters = function applySearchFilters() {
        var $contributions = $(searchBoxConfig.listItems),
            term = $(searchBoxConfig.term).val().trim().toLowerCase(),
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
            $visibleEntries = $contributions.find('td[data-searchable*="' + term + '"]').closest('tr');
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

    global.showUndoWarning = function showUndoWarning(message, feedbackMessage, actionCallback) {
        cornerMessage({
            message: message,
            progressMessage: $T.gettext("Undoing previous operation..."),
            feedbackMessage: feedbackMessage,
            actionLabel: $T.gettext('Undo'),
            actionCallback: actionCallback,
            duration: 10000,
            feedbackDuration: 4000,
            class: 'warning'
        });
    };
})(window);
