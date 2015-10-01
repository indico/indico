(function(global) {
    'use strict';

    $(document).ready(function() {
        setupRegistrationFormScheduleDialogs();
        setupRegistrationFormSummaryPage();
        setupRegistrationsList();
    });

    $(window).scroll(function(){
        IndicoUI.Effect.followScroll();
    });

    function setupRegistrationFormScheduleDialogs() {
        $('a.js-regform-schedule-dialog').on('click', function(e) {
            e.preventDefault();
            ajaxDialog({
                url: $(this).data('href'),
                title: $(this).data('title'),
                onClose: function(data) {
                    if (data) {
                        location.reload();
                    }
                }
            });
        });
    }

    function setupRegistrationFormSummaryPage() {
        $('.js-conditions-dialog').on('click', function(e) {
            e.preventDefault();
            ajaxDialog({
                url: $(this).data('href'),
                title: $(this).data('title')
            });
        });

        $('.js-check-conditions').on('click', function(e) {
            var conditions = $('#conditions-accepted');
            if (conditions.length && !conditions.prop('checked')) {
                var msg = "Please, confirm that you have read and accepted the Terms and Conditions before proceeding.";
                alertPopup($T.gettext(msg), $T.gettext("Terms and Conditions"));
                e.preventDefault();
            }
        });

        $('.js-highlight-payment').on('click', function() {
            $('#payment-summary').effect('highlight', 800);
        });
    }

    function setupRegistrationsList() {
        colorizeSelectedRows();
        $('.registrations .i-table').tablesorter({
            cssAsc:  'header-sort-asc',
            cssDesc: 'header-sort-desc',
            headers: {
                0: {
                    sorter: false
                }
            }
        });
        $('.registrations .toolbar')
        .dropdown()
        .on('click', '.js-dialog-action', function(e) {
            e.preventDefault();
            var $this = $(this);
            ajaxDialog({
                dialogClasses: 'reglist-filter-dialog',
                trigger: this,
                url: $this.data('href'),
                title: $this.data('title'),
                onClose: function(data) {
                    if (data) {
                        $('.registrations-table-wrapper').html(data.registrations_list);
                        colorizeSelectedRows();
                        setupTableSorter();
                    }
                }
            });
        });
    }

    function colorizeSelectedRows() {
        $('table.i-table input.select-row').on('change', function() {
            $(this).closest('tr').toggleClass('selected', $(this).checked);
        });
    }

    function colorizeActiveFilters() {
        $('.reglist-filter .filter').each(function() {
            var $this = $(this);
            if ($this.find(':checked').length) {
                $this.addClass('active');
            }
        });
    }

    global.setupRegistrationsListFilter = function setupRegistrationsListFilter() {
        $('.reglist-filter').dropdown({selector: '.reglist-column .title'});
        colorizeActiveFilters();

        var visibleColumnsRegItemsField = $('#visible-columns-reg-items');
        var visibleColumnsUserInfoField = $('#visible-columns-user-info');
        var regItemsData = JSON.parse(visibleColumnsRegItemsField.val());
        var userInfoData = JSON.parse(visibleColumnsUserInfoField.val());

        $('.reglist-column')
        .on('click', '.trigger', function() {
            var $this = $(this);
            var field = $this.closest('.reglist-column');
            var fieldId = field.data('id');
            var data = field.hasClass('js-user-info') ? userInfoData : regItemsData;
            var visibleColumnsField = field.hasClass('js-user-info') ? visibleColumnsUserInfoField : visibleColumnsRegItemsField;
            var enabled = $this.hasClass('enabled');
            var notEnabled = $this.hasClass('not-enabled');

            if (enabled) {
                data.splice(data.indexOf(fieldId), 1);
            }
            else if (!enabled) {
                data.push(fieldId);
            }
            $this.toggleClass('enabled', !enabled);
            $this.toggleClass('not-enabled', enabled);
            field.toggleClass('striped', enabled);
            visibleColumnsField.val(JSON.stringify(data)).trigger('change');
        })
        .each(function() {
            var field = $(this);
            var fieldId = field.data('id');
            var data = field.hasClass('js-user-info') ? userInfoData : regItemsData;

            if (data.indexOf(fieldId) != -1) {
                field.find('.trigger').addClass('enabled');
            }
            else {
                field.addClass('striped');
                field.find('.trigger').addClass('not-enabled');
            }
        });
    }
})(window);
