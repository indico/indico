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
                var visible;
                if ($content.is(':empty')) {
                    visible = true;
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
                    visible = false;
                    $content.hide();
                    updateMessage(false);

                } else {
                    visible = true;
                    $content.show();
                    updateMessage(true);
                }
                if (!triggeredAutomatically && callback) {
                    callback(visible);
                }
            });
        }
    };

    global.setupCategoryDisplay = function setupCategoryDisplay() {
        'use strict';

        $('.fav-button').on('click', function() {
            var $this = $(this);
            var isFavorite = $this.hasClass('enabled');
            $this.prop('disabled', true);
            $.ajax({
                url: $this.data('href'),
                method: isFavorite ? 'DELETE' : 'PUT',
                error: handleAjaxError,
                success: function() {
                    $this.toggleClass('enabled', !isFavorite);
                },
                complete: function() {
                    $this.prop('disabled', false);
                }
            });
        }).qtip({
            hide: {
                fixed: true,
                delay: 500
            },
            content: {
                text: function() {
                    var $this = $(this);
                    if ($this.hasClass('enabled')) {
                        return $T.gettext("Remove from your favourites");
                    } else {

                        return '<h3>{0}</h3><p>{1}</p>'.format(
                            $T.gettext("Add to your favourites"),
                            $T.gettext('This will make events in this category visible on your <a href="{0}">Dashboard</a>.')
                                 .format($this.data('favorites-href'))
                        );
                    }
                }
            }
        });
    };
})(window);
