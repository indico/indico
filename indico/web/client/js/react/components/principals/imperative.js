// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';

import {FavoritesProvider} from 'indico/react/hooks';
import {injectModal} from 'indico/react/util';

import {UserSearch, GroupSearch} from './Search';

/**
 * Open a user/group/etc. search prompt imperatively.
 */
export function showUserSearch(searchProps = {}, existing = []) {
  return injectModal(resolve => (
    <FavoritesProvider>
      {favoriteUsersController => (
        <UserSearch
          favoritesController={favoriteUsersController}
          existing={existing}
          onAddItems={users => {
            resolve(searchProps.single ? users?.identifier : users.map(u => u.identifier));
          }}
          onClose={() => {
            resolve(searchProps.single ? null : []);
          }}
          defaultOpen
          {...searchProps}
        />
      )}
    </FavoritesProvider>
  ));
}

/**
 * Open a group search prompt imperatively.
 *
 * This mounts the GroupSearch component in a temporary location
 * and returns a promise that will be resolved once something is
 * selected or the dialog is closed (in that case it will be resolved
 * with an empty list of principals)
 */
export function showGroupSearch(searchProps = {}, existing = []) {
  return injectModal(resolve => (
    <GroupSearch
      existing={existing}
      onAddItems={groups => {
        resolve(searchProps.single ? groups?.identifier : groups.map(g => g.identifier));
      }}
      onClose={() => {
        resolve(searchProps.single ? null : []);
      }}
      defaultOpen
      {...searchProps}
    />
  ));
}
