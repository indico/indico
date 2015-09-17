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
                hidePageHeader: true,
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

    global.setupRegistrationsListFilter = function setupRegistrationsListFilter() {
        $('.reglist-filter').dropdown({selector: '.reglist-column .title'});

        var visibleColumnsField = $('#visible-columns');
        var data = JSON.parse(visibleColumnsField.val());

        $('.reglist-column')
        .on('click', '.trigger', function() {
            var field = $(this).closest('.reglist-column');
            var fieldId = field.data('id');
            if ($(this).hasClass('enabled')) {
                data['items'].splice(data['items'].indexOf(fieldId), 1);
            }
            else if ($(this).hasClass('not-enabled')) {
                data['items'].push(fieldId);
            }
            $(this).toggleClass('enabled', !$(this).hasClass('enabled'));
            $(this).toggleClass('not-enabled', !$(this).hasClass('not-enabled'));
            field.toggleClass('striped', !$(this).hasClass('enabled'));
            visibleColumnsField.val(JSON.stringify(data)).trigger('change');
        })
        .each(function() {
            var field = $(this).closest('.reglist-column');
            var fieldId = field.data('id');
            if (data['items'].indexOf(fieldId) != -1) {
                field.find('.trigger').addClass('enabled');
            }
            else {
                field.addClass('striped');
                field.find('.trigger').addClass('not-enabled');
            }
        });
    }
})(window);
