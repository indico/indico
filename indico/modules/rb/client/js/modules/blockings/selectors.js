// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

import {RequestState} from 'indico/utils/redux';

import {isUserAdminOverrideEnabled} from '../../common/user/selectors';

const _getAllBlockings = ({blockings}) => blockings.blockings;
export const getAllBlockings = createSelector(
  _getAllBlockings,
  isUserAdminOverrideEnabled,
  (allBlockings, override) => {
    return _.fromPairs(
      Object.entries(allBlockings).map(([id, allData]) => {
        const {permissions, ...data} = allData;
        const activePermissions =
          override && permissions.admin ? permissions.admin : permissions.user;
        return [id, {...data, ...activePermissions}];
      })
    );
  }
);

export const getBlocking = (state, {blockingId}) => getAllBlockings(state)[blockingId];
export const isFetchingBlockings = ({blockings}) =>
  blockings.requests.blockings.state === RequestState.STARTED;
export const getFilters = ({blockings}) => blockings.filters;
