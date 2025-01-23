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

// import createReduxStore from 'indico/utils/redux';

import {setSessionData, setStaticData, setTimetableData} from './actions';
import {store} from './store';
import Timetable from './Timetable';

(function(global) {
  global.setupTimetable = function setupTimetable() {
    const root = document.querySelector('#timetable-container');
    if (root) {
      const {customLinks} = root.dataset;
      const timetableData = JSON.parse(root.dataset.timetableData);
      const eventInfo = JSON.parse(root.dataset.eventInfo);
      const staticData = {
        eventId: parseInt(eventInfo.id, 10),
        startDt: moment.tz(
          `${eventInfo.startDate.date} ${eventInfo.startDate.time}`,
          eventInfo.startDate.tz
        ),
        endDt: moment.tz(
          `${eventInfo.endDate.date} ${eventInfo.endDate.time}`,
          eventInfo.endDate.tz
        ),
      };
      // const store = createReduxStore('regform-submission', reducers, initialData);
      console.debug(customLinks); // TODO find out what these are
      store.dispatch(setStaticData(staticData));
      store.dispatch(setTimetableData({data: timetableData, eventInfo}));
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
