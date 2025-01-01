// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
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

  const {eventId, sessionId, sessionContribCount} = calendarContainer.dataset;
  const options = [{key: 'session', text: Translate.string('Session'), extraParams: {}}];
  if (parseInt(sessionContribCount, 10) > 0) {
    options.push({
      key: 'contribution',
      text: Translate.string('Detailed timetable'),
      extraParams: {detail: 'contributions'},
    });
  }

  ReactDOM.render(
    <ICSCalendarLink
      endpoint="sessions.export_ics"
      params={{event_id: eventId, session_id: sessionId}}
      renderButton={classes => (
        <IButton icon="calendar" classes={classes} title={Translate.string('Export')} />
      )}
      options={options}
    />,
    calendarContainer
  );
});
