// This file is part of Indico.
// Copyright (C) 2002 - 2024 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {configureStore} from '@reduxjs/toolkit';

import displayReducer from './displaySlice';
import entriesReducer from './entriesSlice';
import experimentalReducer from './experimentalSlice';
import navigationReducer from './navigationSlice';
import openModalReducer from './openModalSlice';
import sessionsReducer from './sessionsSlice';

export const store = configureStore({
  reducer: {
    entries: entriesReducer,
    sessions: sessionsReducer,
    navigation: navigationReducer,
    display: displayReducer,
    openModal: openModalReducer,
    experimental: experimentalReducer,
  },
});

export type TimetableStore = typeof store;
export type RootState = ReturnType<TimetableStore['getState']>;
export type TimetableDispatch = TimetableStore['dispatch'];
