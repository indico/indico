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

    global.setupCategoryCalendar = function setupCategoryCalendar(elementId, categoryURL) {
        var cachedEvents = {};

        $(elementId).fullCalendar({
            firstDay: 1,
            height: 800,
            eventOrder: 'start',
            eventTextColor: '#FFF',
            timeFormat: 'HH:mm',
            nextDayThreshold: '00:00',
            eventLimit: 5,
            eventLimitClick: function(cellInfo) {
                var content = $('<ul>');
                var events = cellInfo.segs.sort(function(a, b) {
                    var aTitle = a.event.title.toLowerCase();
                    var bTitle = b.event.title.toLowerCase();
                    if (aTitle < bTitle) return -1;
                    if (aTitle > bTitle) return 1;
                    return 0;
                });
                $.each(events, function(index, hiddenSegment) {
                    var li = $('<li>');
                    var eventLink = $('<a>', {'href': hiddenSegment.event.url, 'text': hiddenSegment.event.title});
                    li.append(eventLink);
                    content.append(li);
                });
                ajaxDialog({
                    dialogClasses: 'all-events-dialog',
                    title: $T.gettext('Events happening on {0}'.format(cellInfo.date.format('MMMM Do YYYY'))),
                    content: content
                });
            },
            buttonText: {
                'today': $T.gettext('Today')
            },
            events: function(start, end, timezone, callback) {
                function updateCalendar(data) {
                    callback(data.events);
                    var toolbarGroup = $(elementId).find('.fc-toolbar .fc-right');
                    var ongoingEventsInfo = $('<a>', {
                        'href': '#',
                        'class': 'ongoing-events-info',
                        'text': $T.ngettext('{0} long-lasting event not shown',
                                            '{0} long-lasting events not shown', data.ongoing_event_count)
                                  .format(data.ongoing_event_count),
                        'on': {
                            'click': function(evt) {
                                evt.preventDefault();
                                ajaxDialog({
                                    title: $T.gettext('Long lasting events'),
                                    content: $(data.ongoing_events_html),
                                    dialogClasses: 'ongoing-events-dialog'
                                });
                            }
                        }
                    });

                    toolbarGroup.find('.ongoing-events-info').remove();
                    toolbarGroup.prepend(ongoingEventsInfo);
                }

                var key = '{0}-{1}'.format(start, end);
                if (cachedEvents[key]) {
                    updateCalendar(cachedEvents[key]);
                } else {
                    $.ajax({
                        url: categoryURL,
                        data: {start: start.format('YYYY-MM-DD'), end: end.format('YYYY-MM-DD')},
                        dataType: 'json',
                        contentType: 'application/json',
                        error: handleAjaxError,
                        complete: IndicoUI.Dialogs.Util.progress(),
                        success: function(data) {
                            updateCalendar(data);
                            cachedEvents[key] = data;
                        }
                    });
                }
            }
        });
    };
})(window);
