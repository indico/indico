// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';
import {Provider, connect} from 'react-redux';
import UserMenu from '../components/UserMenu';

export default function setupUserMenu(element, store, userInfoSelectors, configSelectors) {
  const Connector = connect(state => ({
    userData: userInfoSelectors.getUserInfo(state),
    languages: configSelectors.getLanguages(state),
    hasLoadedConfig: configSelectors.hasLoadedConfig(state),
    hasLoadedUserInfo: userInfoSelectors.hasLoadedUserInfo(state),
  }))(UserMenu);

  ReactDOM.render(
    <Provider store={store}>
      <Connector />
    </Provider>,
    element
  );
}
