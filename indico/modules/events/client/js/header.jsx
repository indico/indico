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
  const userId = document.querySelector('body').dataset.userId;
  const eventId = document.querySelector('#event-calendar-link').dataset.eventId;

  ReactDOM.render(
    <ICSCalendarLink
      endpoint="events.export_event_ical"
      urlParams={{user_id: userId, event_id: eventId}}
      renderButton={props => (
        <IButton
          icon="calendar"
          classes={{'height-full': true, 'text-color': true, 'subtle': true}}
          {...props}
        />
      )}
      popupPosition="bottom right"
      options={[{key: 'event', text: Translate.string('Event'), queryParams: {}}]}
    />,
    document.querySelector('#event-calendar-link')
  );
});
