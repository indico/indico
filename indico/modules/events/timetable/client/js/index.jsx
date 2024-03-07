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

import {setTimetableData} from './actions';
import reducers from './reducers';
import {timetableData as tData} from './sample-data';
import Timetable from './Timetable';

import 'react-big-calendar/lib/css/react-big-calendar.css';

(function(global) {
  global.setupTimetable = function setupTimetable() {
    const root = document.querySelector('#timetable-container');
    if (root) {
      const {timetableData, eventInfo, customLinks} = root.dataset;
      const initialData = {
        staticData: {
          eventId: parseInt(eventInfo.id, 10),
          startDt: new Date(2023, 4, 8),
          endDt: new Date(2023, 4, 12),
        },
      };
      const store = createReduxStore('regform-submission', reducers, initialData);
      console.debug(customLinks); // TODO find out what these are
      store.dispatch(setTimetableData(tData || JSON.parse(timetableData)));
      ReactDOM.render(
        <Provider store={store}>
          <Timetable />
        </Provider>,
        root
      );
    }
  };
})(window);
