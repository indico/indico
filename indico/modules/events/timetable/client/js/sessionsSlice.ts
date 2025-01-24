// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSlice, PayloadAction} from '@reduxjs/toolkit';

import {changeSessionColor} from './operations';
import {preprocessSessionData} from './preprocess';
import {Session} from './types';

interface SessionsState {
  sessions: Record<number, Session>;
}

const initialState: SessionsState = {
  sessions: [],
}

export const sessionsSlice = createSlice({
  name: 'sessions',
  initialState,
  reducers: {
    setSessionData: (state, action: PayloadAction<any[]>) => {
      state.sessions = preprocessSessionData(action.payload);
    },
    changeColor: (state, action: PayloadAction<{sessionId: number; color: string}>) => {
      if (action.payload.sessionId) {
        state.sessions = changeSessionColor(state, action.payload.sessionId, action.payload.color);
      }
    },
  },
});

export const {setSessionData, changeColor} = sessionsSlice.actions;

export default sessionsSlice.reducer;
