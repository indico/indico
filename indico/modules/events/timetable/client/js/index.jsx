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

import {setCurrentDay, setSessionData, setTimetableData} from './actions';
import reducers from './reducers';
// import {timetableData as tData, eventInfo as eInfo} from './sample-data';
import Timetable from './Timetable';

(function(global) {
  global.setupTimetable = function setupTimetable() {
    const root = document.querySelector('#timetable-container');
    if (root) {
      const timetableData = JSON.parse(root.dataset.timetableData);
      const eventInfo = JSON.parse(root.dataset.eventInfo);
      const initialData = {
        staticData: {
          eventId: parseInt(eventInfo.id, 10),
          startDt: moment.tz(
            `${eventInfo.startDate.date} ${eventInfo.startDate.time}`,
            eventInfo.startDate.tz
          ),
          endDt: moment.tz(
            `${eventInfo.endDate.date} ${eventInfo.endDate.time}`,
            eventInfo.endDate.tz
          ),
        },
      };

      const store = createReduxStore('timetable-management', reducers, initialData);
      store.dispatch(setTimetableData(timetableData, eventInfo));
      store.dispatch(setSessionData(eventInfo.sessions));
      store.dispatch(setCurrentDay(initialData.staticData.startDt));
      ReactDOM.render(
        <Provider store={store}>
          <Timetable />
        </Provider>,
        root
      );
    }
  };
})(window);
