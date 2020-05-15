// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import ReactDOM from 'react-dom';
import React from 'react';
import {Provider} from 'react-redux';
import {OverridableContext} from 'react-overridable';

import setupUserMenu from 'indico/react/containers/UserMenu';

import App from './components/App';
import createRBStore from './store';
import {history} from './history';
import {init} from './actions';
import {actions as configActions, selectors as configSelectors} from './common/config';
import {selectors as userSelectors, actions as userActions} from './common/user';
import {actions as roomsActions} from './common/rooms';
import {actions as linkingActions} from './common/linking';

import 'indico-sui-theme/semantic.css';
import '../styles/main.scss';

export default function setup(overrides = {}, postReducers = []) {
  window.addEventListener(
    'scroll',
    _.debounce(() => {
      document.body.style.setProperty('--offset', window.pageYOffset);
    }, 500)
  );

  document.addEventListener('DOMContentLoaded', () => {
    const appContainer = document.getElementById('rb-app-container');
    const store = createRBStore(postReducers);

    let oldPath = history.location.pathname;
    history.listen(({pathname: newPath}) => {
      if (oldPath.startsWith('/admin') && !newPath.startsWith('/admin')) {
        // user left the admin area so we need to reload some data that might have been changed
        // TODO: add more things here once admins can change them (e.g. map areas)
        store.dispatch(configActions.fetchConfig());
        store.dispatch(roomsActions.fetchEquipmentTypes());
        store.dispatch(roomsActions.fetchRooms());
        store.dispatch(userActions.fetchAllRoomPermissions());
      }
      oldPath = newPath;
    });

    store.dispatch(init());
    store.dispatch(linkingActions.setObjectFromURL(history.location.search.slice(1)));
    setupUserMenu(
      document.getElementById('indico-user-menu-container'),
      store,
      userSelectors,
      configSelectors
    );

    ReactDOM.render(
      <OverridableContext.Provider value={overrides}>
        <Provider store={store}>
          <App history={history} />
        </Provider>
      </OverridableContext.Provider>,
      appContainer
    );
  });
}
