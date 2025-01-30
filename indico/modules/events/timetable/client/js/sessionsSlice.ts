// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSlice, PayloadAction} from '@reduxjs/toolkit';

import * as operations from './operations';
import {preprocessSessionData, SessionData} from './preprocess';
import {Session} from './types';

interface SessionsState {
  sessions: Record<number, Session>;
}

const initialState: SessionsState = {
  sessions: [],
};

export const sessionsSlice = createSlice({
  name: 'sessions',
  initialState,
  reducers: {
    setSessionData: (state, action: PayloadAction<SessionData>) => {
      state.sessions = preprocessSessionData(action.payload);
    },
    changeSessionColor: (state, action: PayloadAction<{sessionId: number; color: string}>) => {
      if (action.payload.sessionId) {
        state.sessions = operations.changeSessionColor(
          state,
          action.payload.sessionId,
          action.payload.color
        );
      }
    },
  },
});

export const {setSessionData, changeSessionColor} = sessionsSlice.actions;

export default sessionsSlice.reducer;
