// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {IButton, ICSCalendarLink} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

document.addEventListener('DOMContentLoaded', () => {
  const calendarContainer = document.querySelector('#event-calendar-link');

  if (!calendarContainer) {
    return;
  }

  const {eventId, eventContribCount} = calendarContainer.dataset;
  const options = [
    {
      key: 'event',
      text: Translate.string('Basic'),
      description: Translate.string('Just the event.'),
      extraParams: {},
    },
  ];
  if (parseInt(eventContribCount, 10) > 0) {
    options.push({
      key: 'contributions',
      text: Translate.string('Detailed'),
      description: Translate.string('A detailed timetable containing individual contributions.'),
      extraParams: {scope: 'contribution'},
    });
    options.push({
      key: 'sessions',
      description: Translate.string('A detailed timetable containing individual session blocks.'),
      text: Translate.string('Compact'),
      extraParams: {scope: 'session'},
    });
  }

  ReactDOM.render(
    <ICSCalendarLink
      endpoint="events.export_event_ical"
      params={{event_id: eventId}}
      renderButton={classes => (
        <IButton
          icon="calendar"
          dropdown
          classes={{'height-full': true, 'text-color': true, 'subtle': true, ...classes}}
          title={Translate.string('Export')}
        />
      )}
      dropdownPosition="top left"
      popupPosition="bottom right"
      options={options}
    />,
    calendarContainer
  );
});
