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

  const eventId = calendarContainer.dataset.eventId;

  ReactDOM.render(
    <ICSCalendarLink
      endpoint="events.export_event_ical"
      urlParams={{event_id: eventId}}
      renderButton={onClick => (
        <IButton
          icon="calendar"
          classes={{'height-full': true, 'text-color': true, 'subtle': true}}
          onClick={onClick}
        />
      )}
      popupPosition="bottom right"
      options={[{key: 'event', text: Translate.string('Event'), queryParams: {}}]}
    />,
    calendarContainer
  );
});
