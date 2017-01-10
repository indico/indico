/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

    global.setupTrackManagement = function setupTrackManagement() {
        var heightLimit = 50;
        $('#track-list-container').on('indico:htmlUpdated', function() {
            var $trackList = $('#track-list');

            $trackList.find('.track-content').each(function() {
                var $this = $(this);
                if ($this.height() > heightLimit) {
                    $this.addClass('track-content-collapsed track-content-collapsible');
                    $this.on('click', function() {
                        $this.toggleClass('track-content-collapsed');
                    });
                }
            });

            $trackList.sortable({
                axis: 'y',
                containment: 'parent',
                cursor: 'move',
                distance: 2,
                handle: '.ui-i-box-sortable-handle',
                items: '> li.track-row',
                tolerance: 'pointer',
                forcePlaceholderSize: true,
                update: function() {
                    var sortedList = $trackList.find('li.track-row').map(function() {
                        return $(this).data('id');
                    }).get();

                    $.ajax({
                        url: $trackList.data('url'),
                        method: 'POST',
                        contentType: 'application/json',
                        data: JSON.stringify({sort_order: sortedList}),
                        complete: IndicoUI.Dialogs.Util.progress(),
                        error: handleAjaxError
                    });
                }
            });
        }).trigger('indico:htmlUpdated');
    };
})(window);

