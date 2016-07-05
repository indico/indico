/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

(function(global) {
    'use strict';

    global.setupCategoryDisplayEventList = function setupCategoryDisplayEventList(showPastEvents) {
        var $eventList = $('.event-list');
        var $futureEvents = $eventList.find('.future-events');
        var $pastEvents = $eventList.find('.past-events');

        setupToggleEventListButton($futureEvents);
        setupToggleEventListButton($pastEvents, onTogglePastEvents);

        if (showPastEvents) {
            $pastEvents.find('.js-toggle-list').first().trigger('click', true);
        }

        function onTogglePastEvents(shown) {
            $.ajax({
                url: $eventList.data('show-past-events-url'),
                method: shown ? 'PUT' : 'DELETE',
                error: handleAjaxError
            });
        }

        function setupToggleEventListButton(wrapper, callback) {
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

            $wrapper.find('.js-toggle-list').on('click', function(evt, triggeredAutomatically) {
                evt.preventDefault();
                var isEmpty = $content.is(':empty');
                if (isEmpty) {
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
                if (!triggeredAutomatically) {
                    callback(isEmpty);
                }
            });
        }
    };
})(window);
