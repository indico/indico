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
            var $this = $(this);
            if ($this.data('count')) {
                $this.closest('tr').toggleClass('selected').nextUntil('tr:not(.session-blocks-row)', 'tr').toggle();
            }
        });

        $('.js-submit-session-form').on('click', function(evt) {
            evt.preventDefault();
            var $this = $(this);

            if (!$this.hasClass('disabled')) {
                $('#sessions-wrapper form').attr('action', $this.data('href')).submit();
            }
        });
    };
})(window);
