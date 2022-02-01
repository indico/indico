// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {getStaticData} from '../form/selectors';

export const getUserInfo = createSelector(
  getStaticData,
  staticData => staticData.userInfo
);

/** Indicates whether we are updating the registration */
export const getUpdateMode = createSelector(
  getStaticData,
  staticData => !!staticData.registrationUuid
);

/** Indicates whether the registration is moderated */
export const getModeration = createSelector(
  getStaticData,
  staticData => staticData.moderated
);
