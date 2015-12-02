(function(global) {
    'use strict';

    function handleRowSelection() {
        $('.sessions-wrapper').on('change', '.select-row', function() {
            $(this).closest('tr').toggleClass('selected', this.checked);
            $('.js-requires-selected-row').toggleClass('disabled', !$('.sessions input:checkbox:checked').length);
        }).trigger('change');
    }

    function setupTableSorter() {
        $('.sessions .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            cssInfoBlock: 'avoid-sort',
            cssChildRow: 'session-blocks-row',
            headerTemplate: '',
            sortList: [[1, 0]]
        });
    }

    global.setupSessionsList = function setupSessionsList() {
        handleRowSelection();
        setupTableSorter();

        $('.sessions').on('click', '#select-all', function() {
            $('.sessions-wrapper table.i-table input.select-row').prop('checked', true).trigger('change');
        });

        $('.sessions').on('click', '#select-none', function() {
            $('table.i-table input.select-row').prop('checked', false).trigger('change');
        });

        $('.sessions .toolbar').on('click', '.disabled', function(evt) {
            evt.preventDefault();
            evt.stopPropagation();
        });

        $('.sessions').on('click', '.js-show-sessions', function() {
            $(this).closest('tr').nextUntil('tr:not(.session-blocks-row)', 'tr').toggle();
        });
    }
})(window);
