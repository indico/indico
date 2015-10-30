(function(global) {
    'use strict';

    $(document).ready(function() {
        setupRegistrationFormScheduleDialogs();
        setupRegistrationFormSummaryPage();
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

        $('.js-modify-payment').on('click', function() {
            var $this = $(this);
            $.ajax({
                method: 'POST',
                url: $this.data('href'),
                error: handleAjaxError,
                complete: IndicoUI.Dialogs.Util.progress(),
                data: {pay: $this.data('pay')},
                success: function(data) {
                    $('.management-page').html(data.html);
                }
            });
        });

        $('.management-page').on('indico:confirmed', '.js-toggle-checked-in, .js-moderate', function(evt) {
            evt.preventDefault();

            var $this = $(this);
            $.ajax({
                method: $this.data('method'),
                url: $this.data('href'),
                error: handleAjaxError,
                complete: IndicoUI.Dialogs.Util.progress(),
                success: function(data) {
                    $('.management-page').html(data.html);
                }
            });
        });

        $('.registrations .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            headerTemplate: ''
        });
    }

    global.setupRegistrationFormListPage = function setupRegistrationFormListPage() {
        $('#payment-disabled-notice').on('indico:confirmed', '.js-enable-payments', function(evt) {
            evt.preventDefault();

            var $this = $(this);
            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function() {
                    $('#payment-disabled-notice').remove();
                }
            });
        });
    };
})(window);
