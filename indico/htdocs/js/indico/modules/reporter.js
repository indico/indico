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

    function setupFilterDialog() {
        $('.js-customize-report').each(function() {
            var $this = $(this);
            $this.ajaxDialog({
                dialogClasses: 'report-filter-dialog',
                onClose: function(data) {
                    if (data) {
                        var reportSection = $this.closest('.report-section');
                        reportSection.find('.report').html(data.html);
                        reportSection.find('.displayed-records-fragment').html(data.displayed_records_fragment);
                    }
                }
            });
        });
    }

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
        setupFilterDialog();
        setupStaticURLGeneration();
    };
})(window);
