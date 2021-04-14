// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import 'fullcalendar';
import 'fullcalendar/dist/fullcalendar.css';

(function(global) {
  global.setupCategoryCalendar = function setupCategoryCalendar(elementId, categoryURL) {
    const cachedEvents = {};

    $(elementId).fullCalendar({
      firstDay: 1,
      height: 800,
      eventOrder: 'start',
      eventTextColor: '#FFF',
      timeFormat: 'HH:mm',
      nextDayThreshold: '00:00',
      eventLimit: 5,
      buttonText: {
        today: $T.gettext('Today'),
      },
      eventLimitClick(cellInfo) {
        const content = $('<ul>');
        const events = cellInfo.segs.sort((a, b) => {
          const aTitle = a.footprint.eventInstance.def.title.toLowerCase();
          const bTitle = b.footprint.eventInstance.def.title.toLowerCase();
          if (aTitle < bTitle) {
            return -1;
          }
          if (aTitle > bTitle) {
            return 1;
          }
          return 0;
        });
        events.forEach(hiddenSegment => {
          const li = $('<li>');
          const eventLink = $('<a>', {
            href: hiddenSegment.footprint.eventInstance.def.url,
            text: hiddenSegment.footprint.eventInstance.def.title,
          });
          li.append(eventLink);
          content.append(li);
        });
        ajaxDialog({
          dialogClasses: 'all-events-dialog',
          title: $T.gettext('Events happening on {0}').format(cellInfo.date.format('MMMM Do YYYY')),
          content,
        });
      },
      events(start, end, timezone, callback) {
        function updateCalendar(data) {
          callback(data.events);
          const toolbarGroup = $(elementId).find('.fc-toolbar .fc-right');
          const ongoingEventsInfo = $('<a>', {
            href: '#',
            class: 'ongoing-events-info',
            text: $T
              .ngettext(
                '{0} long-lasting event not shown',
                '{0} long-lasting events not shown',
                data.ongoing_event_count
              )
              .format(data.ongoing_event_count),
            on: {
              click: evt => {
                evt.preventDefault();
                ajaxDialog({
                  title: $T.gettext('Long lasting events'),
                  content: $(data.ongoing_events_html),
                  dialogClasses: 'ongoing-events-dialog',
                });
              },
            },
          });

          toolbarGroup.find('.ongoing-events-info').remove();
          toolbarGroup.prepend(ongoingEventsInfo);
        }

        const key = `${start}-${end}`;
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
            success(data) {
              updateCalendar(data);
              cachedEvents[key] = data;
            },
          });
        }
      },
    });
  };
})(window);
