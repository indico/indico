// This file is part of Indico.
// Copyright (C) 2002 - 2026 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import moment from 'moment';
import React from 'react';
import ReactDOM from 'react-dom';
import {Provider} from 'react-redux';

import {UserSearchTokenContext} from 'indico/react/components/principals/Search';
import createReduxStore from 'indico/utils/redux';

import {setSessionData, setTimetableData} from './actions';
import {ModalProvider} from './ModalContext';
import reducers from './reducers';
import Timetable from './Timetable';
import {getCurrentDateLocalStorage} from './utils';

(function(global) {
  global.setupTimetable = function setupTimetable() {
    const root = document.querySelector('#timetable-container');
    if (root) {
      const searchToken = root.dataset.searchToken;
      const timetableData = JSON.parse(root.dataset.timetableData);
      const eventInfo = JSON.parse(root.dataset.eventInfo);
      const eventId = parseInt(eventInfo.id, 10);
      const startDt = moment(eventInfo.start_dt_local);
      const currentDate = getCurrentDateLocalStorage(eventId) || moment(startDt);
      const initialData = {
        staticData: {
          eventId,
          eventType: eventInfo.type,
          startDt: moment(eventInfo.start_dt_local),
          endDt: moment(eventInfo.end_dt_local),
          defaultContribDurationMinutes: eventInfo.default_contribution_duration / 60,
          eventLocationParent: eventInfo.location_parent,
        },
        navigation: {
          isDraft: eventInfo.is_draft,
          currentDate,
          // Refers to when a user clicks to view a session block as a timetable
          expandedSessionBlockId: null,
        },
      };

      const store = createReduxStore('timetable-management', reducers, initialData);
      store.dispatch(setTimetableData(timetableData, eventInfo));
      store.dispatch(setSessionData(eventInfo.sessions));
      ReactDOM.render(
        <Provider store={store}>
          <UserSearchTokenContext.Provider value={searchToken}>
            <ModalProvider>
              <Timetable />
            </ModalProvider>
          </UserSearchTokenContext.Provider>
        </Provider>,
        root
      );
    }
  };
})(window);
