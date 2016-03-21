(function(global) {
    'use strict';

    $(document).ready(function() {
        setupRegistrationFormScheduleDialogs();
        setupRegistrationFormSummaryPage();
        $('.js-sortable-list-widget').each(function() {
            setupRegistrationSortableLists($(this));
        });
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

    global.setupRegistrationFormListPage = function setupRegistrationFormListPage() {
        $('#payment-disabled-notice').on('indico:confirmed', '.js-enable-payments', function(evt) {
            evt.preventDefault();

            var $this = $(this);
            $.ajax({
                url: $this.data('href'),
                method: $this.data('method'),
                complete: IndicoUI.Dialogs.Util.progress(),
                error: handleAjaxError,
                success: function(data) {
                    $('#payment-disabled-notice').remove();
                    $('#event-sidemenu').html(data.event_menu);
                }
            });
        });
    };

    global.setupRegistrationSortableLists = function setupRegistrationSortableLists($wrapper) {
        /* Works with the sortable_lists macro defined in
         * indico/modules/events/registration/templates/management/_sortable_list.html
         *
         * Global needed to call it on sortable lists in dialog
         */

        // Render the lists sortable
        if ($wrapper.data('disable-dragging') === undefined) {
            var $lists = $wrapper.find('ul');
            $lists.sortable({
                connectWith: $lists,
                placeholder: 'i-label sortable-item placeholder',
                containment: $wrapper,
                forcePlaceholderSize: true
            });
        }

        // Move an item from the enabled list to the disabled one (or vice versa).
        function toggleEnabled($li) {
            var $list = $li.closest('ul');
            var targetClass = $list.hasClass('enabled') ? '.disabled' : '.enabled';
            var $destination = $list.closest('.js-sortable-list-widget').find('ul' + targetClass);
            $li.detach().appendTo($destination);
        }

        $wrapper.find('ul li .toggle-enabled').on('click', function() {
            toggleEnabled($(this).closest('li'));
        });

        // Prevents dragging the row when the action buttons are clicked.
        $wrapper.find('.actions').on('mousedown', function(evt) {
            evt.stopPropagation();
        });
    };
})(window);
