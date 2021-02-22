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
  const calendarContainer = document.querySelector('#session-calendar-link');

  if (!calendarContainer) {
    return;
  }

  const userId = document.body.dataset.userId;
  const {eventId, sessionId} = calendarContainer.dataset;

  ReactDOM.render(
    <ICSCalendarLink
      endpoint="sessions.export_ics"
      urlParams={{user_id: userId, event_id: eventId, session_id: sessionId}}
      renderButton={onClick => <IButton icon="calendar" onClick={onClick} />}
      options={[{key: 'session', text: Translate.string('Session'), queryParams: {}}]}
    />,
    calendarContainer
  );
});
