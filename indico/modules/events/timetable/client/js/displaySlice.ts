// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSlice, PayloadAction} from '@reduxjs/toolkit';

type Mode = 'compact' | 'full';

interface DisplayState {
  mode: Mode;
  showUnscheduled: boolean;
  showAllTimeslots: boolean;
}

const initialState: DisplayState = {
  mode: 'compact',
  showUnscheduled: false,
  showAllTimeslots: false,
};

export const displaySlice = createSlice({
  name: 'display',
  initialState,
  reducers: {
    setDisplayMode: (state, action: PayloadAction<Mode>) => {
      state.mode = action.payload;
    },
    toggleShowUnscheduled: state => {
      state.showUnscheduled = !state.showUnscheduled;
    },
    toggleShowAllTimeslots: state => {
      state.showAllTimeslots = !state.showAllTimeslots;
    },
  },
});

export const {setDisplayMode, toggleShowUnscheduled, toggleShowAllTimeslots} = displaySlice.actions;

export default displaySlice.reducer;
