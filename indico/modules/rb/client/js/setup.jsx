// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import {OverridableContext} from 'react-overridable';
import {Provider, useSelector} from 'react-redux';

import {UserSearchTokenContext} from 'indico/react/components/principals/Search';
import setupUserMenu from 'indico/react/containers/UserMenu';

import {init} from './actions';
import {actions as configActions, selectors as configSelectors} from './common/config';
import {actions as linkingActions} from './common/linking';
import {actions as roomsActions} from './common/rooms';
import {selectors as userSelectors, actions as userActions} from './common/user';
import App from './components/App';
import {history} from './history';
import createRBStore from './store';

import 'indico-sui-theme/semantic.css';
import '../styles/main.scss';

function UserSearchTokenProvider({children}) {
  const userSearchToken = useSelector(userSelectors.getSearchToken);
  return (
    <UserSearchTokenContext.Provider value={userSearchToken}>
      {children}
    </UserSearchTokenContext.Provider>
  );
}

UserSearchTokenProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

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
      configSelectors,
      UserSearchTokenProvider
    );

    ReactDOM.render(
      <OverridableContext.Provider value={overrides}>
        <Provider store={store}>
          <UserSearchTokenProvider>
            <App history={history} />
          </UserSearchTokenProvider>
        </Provider>
      </OverridableContext.Provider>,
      appContainer
    );
  });
}
