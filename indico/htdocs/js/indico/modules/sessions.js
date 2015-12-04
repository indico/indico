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

    function setupPalettePickers() {
        $('.js-color-switch').each(function() {
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
                        traditional: true,
                        error: handleAjaxError,
                        complete: IndicoUI.Dialogs.Util.progress()
                    });
                }
            });
        });
    }

    global.setupSessionsList = function setupSessionsList() {
        handleRowSelection();
        setupTableSorter();
        setupPalettePickers();

        $('.sessions .toolbar').on('click', '.disabled', function(evt) {
            evt.preventDefault();
            evt.stopPropagation();
        });

        function updateSessionsListOnSuccess(data) {
            if (data) {
                $('.sessions-wrapper').html(data.session_list);
                setupTableSorter();
                setupPalettePickers();
            }
        }

        $('.sessions').on('click', '#add-new-session', function() {
            var $this = $(this);
            ajaxDialog({
                url: $this.data('href'),
                title: $this.data('title'),
                onClose: updateSessionsListOnSuccess
            });
        });

        $('.sessions').on('click', '.edit-session', function() {
            var $this = $(this);
            ajaxDialog({
                url: $this.data('href'),
                title: $this.data('title'),
                onClose: updateSessionsListOnSuccess
            });
        });

        $('.sessions').on('click', '.show-session-blocks', function() {
            $(this).closest('tr').toggleClass('selected').nextUntil('tr:not(.session-blocks-row)', 'tr').toggle();
        });

        $('.sessions').on('indico:confirmed', '#remove-selected-sessions', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            var sessionIds = $('.sessions input:checkbox:checked').map(function() {
                return $(this).val();
            }).get();

            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                error: handleAjaxError,
                traditional: true,
                data: {session_ids: sessionIds},
                success: updateSessionsListOnSuccess
            });
        });

        $('.sessions').on('indico:confirmed', '.js-remove-session', function(evt) {
            evt.preventDefault();
            var $this = $(this);

            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                data: {session_ids: $this.data('session-id')},
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: updateSessionsListOnSuccess
            });
        });

        $('.sessions').on('click', '.js-export-sessions', function(evt) {
            evt.preventDefault();
            var $this = $(this);
            var checkedItems = $.map($('.sessions input:checkbox:checked'), function() {
                return $(this).val();
            });

            $.ajax({
                url: $this.data('href'),
                method: 'POST',
                traditional: true,
                error: handleAjaxError,
                data: {session_ids: checkedItems}
            });
        });
    };

})(window);
