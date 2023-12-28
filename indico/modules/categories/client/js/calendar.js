// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/* global handleAjaxError:false, ajaxDialog:false */

import {Calendar} from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';

import React from 'react';
import ReactDOM from 'react-dom';

import {$T} from 'indico/utils/i18n';
import CalendarLegend from './components/CalendarLegend';

(function(global) {
  global.setupCategoryCalendar = function setupCategoryCalendar(
    containerCalendarSelector,
    containerLegendSelector,
    tz,
    categoryURL
  ) {
    const cachedEvents = {};
    const container = document.querySelector(containerCalendarSelector);
    const calendar = new Calendar(container, {
      headerToolbar: {
        start: 'prev,next today',
        center: 'title',
        end: 'dayGridMonth,dayGridWeek,dayGridDay',
      },
      plugins: [dayGridPlugin],
      initialView: 'dayGridMonth',
      timeZone: tz,
      firstDay: 1,
      height: 850,
      eventOrder: 'start',
      eventTextColor: '#FFF',
      eventTimeFormat: {
        // most convoluted way of writing HH:MM...
        hour: '2-digit',
        minute: '2-digit',
        meridiem: false,
        hour12: false,
      },
      nextDayThreshold: '00:00',
      dayMaxEvents: true,
      buttonText: {
        today: $T.gettext('Today'),
      },
      events({start, end}, successCallback, failureCallback) {
        function updateCalendar(data) {
          successCallback(data.events);
          const toolbarGroup = $(containerCalendarSelector).find(
            '.fc-toolbar .fc-toolbar-chunk:last-child'
          );
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
          if (data.ongoing_event_count) {
            toolbarGroup.prepend(ongoingEventsInfo);
          }
        }

        function setupCalendarLegend (items, container){
          ReactDOM.render(
            React.createElement(CalendarLegend, { items }),
            container
          );
        }

        function updateLegend(data) {
          const categoryMap = data.categories.reduce((acc, value) => ({
            ...acc,
            [value.id]: value.title,
          }), {});
          const usedCategories = new Set();
          const categories = data.events
            .reduce((acc, value) => {
              if (usedCategories.has(value.categoryId)) {
                return acc;
              }
              usedCategories.add(value.categoryId);
              return [
                ...acc,
                {
                  title: categoryMap[value.categoryId],
                  textColor: value.textColor,
                  color: value.color,
                  id: value.categoryId
                },
              ];
            }, [])
            .sort((a, b) => a.title.localeCompare(b.title));
          setupCalendarLegend(categories, document.getElementById(containerLegendSelector));
        }

        start = start.toISOString().substring(0, 10);
        end = end.toISOString().substring(0, 10);
        const key = `${start}-${end}`;
        if (cachedEvents[key]) {
          updateLegend(cachedEvents[key]);
          updateCalendar(cachedEvents[key]);
        } else {
          $.ajax({
            url: categoryURL,
            data: {start, end},
            dataType: 'json',
            contentType: 'application/json',
            complete: IndicoUI.Dialogs.Util.progress(),
            success(data) {
              updateLegend(data);
              updateCalendar(data);
              cachedEvents[key] = data;
            },
            error(error) {
              failureCallback(new Error('Loading events failed'));
              handleAjaxError(error);
            },
          });
        }
      },
    });
    calendar.render();

    $('.js-calendar-datepicker').datepicker({
      dateFormat: 'yy-mm-dd',
      beforeShowDay(date) {
        return [date.getDate() === 1, ''];
      },
      onSelect(date) {
        calendar.gotoDate(date);
      },
    });
  };
})(window);
