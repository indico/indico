(function(global) {
    'use strict';

    function colorizeFilter(filter) {
        filter.toggleClass('active', filter.find(':checked').length > 0);
    }

    function colorizeActiveFilters() {
        $('.report-filter .filter').each(function() {
            colorizeFilter($(this));
        });
    }

    function handleRowSelection() {
        $('table.i-table input.select-row').on('change', function() {
            $(this).closest('tr').toggleClass('selected', this.checked);
        }).trigger('change');
    }

    global.setupReportFilter = function() {
        $('.report-filter').dropdown({selector: '.report-column .title'});

        colorizeActiveFilters();

        $('.report-filter-dialog .js-reset-btn').on('click', function() {
            $('.report-filter input:checkbox:checked').prop('checked', false).trigger('change');
            $('.js-clear-filters-message').slideDown({
                done: function() {
                    $(this).delay(4000).slideUp();
                }
            });
        });

        $('.report-filter input:checkbox').on('change', function() {
            colorizeFilter($(this).closest('.filter'));
        });
    };

    function setupStaticURLGeneration() {
        $('.js-static-url').on('click', function() {
            var $this = $(this);
            $.ajax({
                method: 'POST',
                url: $this.data('href'),
                error: handleAjaxError,
                complete: IndicoUI.Dialogs.Util.progress(),
                success: function(data) {
                    $this.copyURLTooltip(data.url);
                }
            });
        });
    }

    global.setupReporter = function() {
        setupStaticURLGeneration();
        handleRowSelection();

        $('.report').on('indico:htmlUpdated', function() {
            handleRowSelection();
        });
    };
})(window);
