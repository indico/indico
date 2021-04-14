// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import React from 'react';
import ReactDOM from 'react-dom';

import {FavoritesProvider} from 'indico/react/hooks';

import {UserSearch} from './Search';

/**
 * Open a user/group/etc. search prompt imperatively.
 *
 * This mounts the UserSearch component in a temporary location
 * and returns a promise that will be resolved once something is
 * selected or the dialog is closed (in that case it will be resolved
 * with an empty list of principals)
 */
export function showUserSearch(searchProps = {}) {
  const container = document.createElement('div');
  document.body.appendChild(container);

  const cleanup = () =>
    _.defer(() => {
      ReactDOM.unmountComponentAtNode(container);
      document.body.removeChild(container);
    });

  return new Promise(resolve => {
    ReactDOM.render(
      <FavoritesProvider>
        {([favorites]) => (
          <UserSearch
            favorites={favorites}
            existing={[]}
            onAddItems={users => {
              resolve(searchProps.single ? users?.identifier : users.map(u => u.identifier));
              cleanup();
            }}
            onClose={() => {
              resolve(searchProps.single ? null : []);
              cleanup();
            }}
            defaultOpen
            {...searchProps}
          />
        )}
      </FavoritesProvider>,
      container
    );
  });
}
