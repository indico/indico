// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import createReduxStore from 'indico/utils/redux';

import {setSessionData, setTimetableData} from './actions';
import reducers from './reducers';
import {timetableData as tData, eventInfo as eInfo} from './sample-data';
import Timetable from './Timetable';

import 'react-big-calendar/lib/css/react-big-calendar.css';

const DEBUG_MODE = false; //TODO: remove

(function(global) {
  global.setupTimetable = function setupTimetable() {
    const root = document.querySelector('#timetable-container');
    if (root) {
      const {customLinks} = root.dataset;
      const timetableData = DEBUG_MODE ? tData : JSON.parse(root.dataset.timetableData);
      const eventInfo = DEBUG_MODE ? eInfo : JSON.parse(root.dataset.eventInfo);
      const initialData = {
        staticData: {
          eventId: parseInt(eventInfo.id, 10),
          startDt: DEBUG_MODE ? new Date(2023, 4, 8) : new Date(eventInfo.startDate.date), // TODO handle tz
          endDt: DEBUG_MODE ? new Date(2023, 4, 12) : new Date(eventInfo.endDate.date), // TODO handle tz
        },
      };
      const store = createReduxStore('regform-submission', reducers, initialData);
      console.debug(customLinks); // TODO find out what these are
      store.dispatch(setTimetableData(timetableData));
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
