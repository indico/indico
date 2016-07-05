function setupCategoryDisplayEventList(show_past_events) {
    'use strict';

    var $eventList = $('.event-list');
    var $futureEvents = $eventList.find('.future-events');
    var $pastEvents = $eventList.find('.past-events');

    setupToggleEventListButton($futureEvents);
    setupToggleEventListButton($pastEvents);

    if (show_past_events) {
        $pastEvents.find('.js-toggle-list').first().trigger('click');
    }

    function setupToggleEventListButton(wrapper) {
        var $wrapper = $(wrapper);
        var $content = $wrapper.find('.events');

        function updateMessage(visible) {
            $wrapper.find('.js-hide-message').toggle(visible);
            $wrapper.find('.js-show-message').toggle(!visible);
        }
        updateMessage(!$content.is(':empty'));

        function displaySpinner(visible) {
            $wrapper.find('.js-toggle-list').toggle(!visible);
            $wrapper.find('.js-spinner').toggle(visible);
        }
        displaySpinner(false);

        $wrapper.find('.js-toggle-list').on('click', function(evt) {
            evt.preventDefault();
            if ($content.is(':empty')) {
                displaySpinner(true);
                $.ajax({
                    url: $content.data('event-list-url'),
                    data: {
                        before: $content.data('event-list-before'),
                        after: $content.data('event-list-after')
                    },
                    error: handleAjaxError,
                    success: function(data) {
                        $content.html(data.html);
                        $content.show();
                        updateMessage(true);
                        displaySpinner(false);
                    }
                });
            } else if ($content.is(':visible')) {
                $content.hide();
                updateMessage(false);
            } else {
                $content.show();
                updateMessage(true);
            }
        });
    }
}
