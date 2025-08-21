// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import createReduxStore from 'indico/utils/redux';

import {setSessionData, setTimetableData} from './actions';
import reducers from './reducers';
import Timetable from './Timetable';
import {getCurrentDateLocalStorage} from './utils';

(function(global) {
  global.setupTimetable = function setupTimetable() {
    const root = document.querySelector('#timetable-container');
    if (root) {
      const timetableData = JSON.parse(root.dataset.timetableData);
      const eventInfo = JSON.parse(root.dataset.eventInfo);
      const eventId = parseInt(eventInfo.id, 10);
      const startDt = moment.tz(
        `${eventInfo.startDate.date} ${eventInfo.startDate.time}`,
        eventInfo.startDate.tz
      );
      const currentDate = getCurrentDateLocalStorage(eventId) || startDt;
      const initialData = {
        staticData: {
          eventId,
          startDt,
          endDt: moment.tz(
            `${eventInfo.endDate.date} ${eventInfo.endDate.time}`,
            eventInfo.endDate.tz
          ),
          defaultContribDurationMinutes: eventInfo.defaultContribDurationMinutes,
        },
        navigation: {
          isDraft: eventInfo.isDraft,
          currentDate,
        },
      };

      const store = createReduxStore('timetable-management', reducers, initialData);
      store.dispatch(setTimetableData(timetableData, eventInfo));
      store.dispatch(setSessionData(eventInfo.sessions));
      ReactDOM.render(
        <Provider store={store}>
          <Timetable />
        </Provider>,
        root
      );
    }
  };
})(window);
