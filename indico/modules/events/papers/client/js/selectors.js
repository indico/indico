// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {RequestState} from 'indico/utils/redux';

export const isFetchingPaperDetails = state =>
  state.paper.requests.details.state === RequestState.STARTED;
export const isFetchingPaperPermissions = state =>
  state.paper.requests.permissions.state === RequestState.STARTED;
export const isJudgingInProgress = state =>
  state.paper.requests.judgment.state === RequestState.STARTED;

export const getPaperDetails = state => state.paper.details;
export const getPaperEvent = state => state.paper.details.event;
export const getPaperContribution = state => state.paper.details.contribution;
export const getCurrentUser = state => state.staticData.user;
export const getPaperPermissions = state => state.paper.permissions;
export const isEventLocked = state => state.paper.details.event.isLocked;
