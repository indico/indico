// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import {ICSCalendarLink} from 'indico/react/components';
import {Translate} from 'indico/react/i18n';

let calendarExportContainer = null;
let isOpen = false;

document.addEventListener('indico:action:event-export-calendar', e => {
  if (isOpen) {
    return;
  }

  isOpen = true;

  const {eventId, eventContribCount, eventSessionBlockCount, eventInSeries} = e.detail;
  const options = [
    {
      key: 'event',
      text: Translate.string('Basic'),
      description: Translate.string('Just the event.'),
      extraParams: {},
    },
  ];
  if (parseInt(eventSessionBlockCount, 10) > 0) {
    options.push({
      key: 'sessions',
      description: Translate.string(
        'A detailed timetable containing individual session blocks and top-level contributions.'
      ),
      text: Translate.string('Compact'),
      extraParams: {scope: 'session'},
    });
  }
  if (parseInt(eventContribCount, 10) > 0) {
    options.push({
      key: 'contributions',
      text: Translate.string('Detailed'),
      description: Translate.string(
        'A detailed timetable containing all individual contributions.'
      ),
      extraParams: {scope: 'contribution'},
    });
  }

  // Create container once and reuse it
  if (!calendarExportContainer) {
    calendarExportContainer = document.createElement('div');
    calendarExportContainer.style.display = 'inline-block';
    e.detail.trigger.after(calendarExportContainer);
  }

  const handleCleanup = () => {
    ReactDOM.unmountComponentAtNode(calendarExportContainer);
    setTimeout(() => {
      isOpen = false;
    });
  };

  ReactDOM.render(
    <ICSCalendarLink.Static
      endpoint="events.export_event_ical"
      params={{event_id: eventId}}
      options={options}
      eventInSeries={eventInSeries !== undefined}
      onClose={handleCleanup}
      triggerElement={e.detail.trigger}
    />,
    calendarExportContainer
  );
});
