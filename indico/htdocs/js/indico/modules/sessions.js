(function(global) {
    'use strict';

    function setupTableSorter() {
        $('#sessions .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            cssInfoBlock: 'avoid-sort',
            cssChildRow: 'session-blocks-row',
            headerTemplate: '',
            sortList: [[1, 0]]
        });
    }

    function setupPalettePickers() {
        $('.palette-picker-trigger').each(function() {
            var $this = $(this);
            $this.palettepicker({
                availableColors: $this.data('colors'),
                onSelect: function(background, text) {
                    $.ajax({
                        url: $(this).data('href'),
                        method: $(this).data('method'),
                        data: JSON.stringify({'colors': {'text': text, 'background': background}}),
                        dataType: 'json',
                        contentType: 'application/json',
                        error: handleAjaxError,
                        complete: IndicoUI.Dialogs.Util.progress()
                    });
                }
            });
        });
    }

    global.setupSessionsList = function setupSessionsList() {
        enableIfChecked('#sessions-wrapper', '.select-row', '#sessions .js-requires-selected-row');
        setupTableSorter();
        setupPalettePickers();

        $('#sessions .toolbar').on('click', '.disabled', function(evt) {
            evt.preventDefault();
            evt.stopPropagation();
        });

        $('#sessions').on('indico:htmlUpdated', function() {
            setupTableSorter();
            setupPalettePickers();
        }).on('click', '.show-session-blocks', function() {
            $(this).closest('tr').toggleClass('selected').nextUntil('tr:not(.session-blocks-row)', 'tr').toggle();
        });

        $('.js-submit-session-form').on('click', function(evt) {
            evt.preventDefault();
            var $this = $(this);

            if (!$this.hasClass('disabled')) {
                $('#sessions-wrapper form').attr('action', $this.data('href')).submit();
            }
        });
    };

    global.setupSessionPersonsList = function setupSessionPersonsList() {
        enableIfChecked('#persons-list', '.select-row', '#persons-list .js-requires-selected-row');
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

})(window);
