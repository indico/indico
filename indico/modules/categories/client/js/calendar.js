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

import {Translate} from 'indico/react/i18n';
import {$T} from 'indico/utils/i18n';

import CalendarLegend from './components/CalendarLegend';

(function(global) {
  let groupBy = 'category';
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

        function setupCalendarLegend(data, items, legendContainer) {
          const onFilterChanged = filterBy => {
            groupBy = filterBy;
            calendar.refetchEvents();
          };
          ReactDOM.render(
            <CalendarLegend
              items={items}
              groupBy={data.group_by}
              onFilterChanged={onFilterChanged}
            />,
            legendContainer
          );
        }

        function setupLegendByAttribute(events, items, attr, defaultTitle) {
          const itemMap = items.reduce(
            (acc, {id, title}) => ({
              ...acc,
              [id]: title ?? defaultTitle,
            }),
            {}
          );
          const usedItems = new Set();
          return events
            .reduce((acc, value) => {
              const id = value[attr] ?? 0;
              if (usedItems.has(id)) {
                return acc;
              }
              usedItems.add(id);
              return [
                ...acc,
                {
                  title: itemMap[id] ?? defaultTitle,
                  textColor: value.textColor,
                  color: value.color,
                  id,
                },
              ];
            }, [])
            .sort((a, b) => a.title.localeCompare(b.title));
        }

        function updateLegend(data) {
          let items;
          switch (data.group_by) {
            case 'category':
              items = setupLegendByAttribute(
                data.events,
                data.categories,
                'categoryId',
                Translate.string('No category')
              );
              break;
            case 'location':
              items = setupLegendByAttribute(
                data.events,
                data.locations,
                'venueId',
                Translate.string('No location')
              );
              break;
            default:
              items = [];
              break;
          }
          setupCalendarLegend(data, items, document.getElementById(containerLegendSelector));
        }

        start = start.toISOString().substring(0, 10);
        end = end.toISOString().substring(0, 10);
        const key = `${start}-${end}-${groupBy}`;
        if (cachedEvents[key]) {
          updateLegend(cachedEvents[key]);
          updateCalendar(cachedEvents[key]);
        } else {
          $.ajax({
            url: categoryURL,
            data: {start, end, group_by: groupBy},
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
