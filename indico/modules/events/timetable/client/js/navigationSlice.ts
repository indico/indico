// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSlice, PayloadAction} from '@reduxjs/toolkit';

interface NavigationState {
  numDays: number; // Number of days that fit on the toolbar
  offset: number; // Currently selected offset starting from the first day
}

const initialState: NavigationState = {
  numDays: 2,
  offset: 0,
};

export const navigationSlice = createSlice({
  name: 'navigation',
  initialState,
  reducers: {
    scrollNavbar: (state, action: PayloadAction<number>) => {
      state.offset = action.payload;
    },
    resizeWindow: (state, action: PayloadAction<{newSize: number; dayIdx: number}>) => {
      state.numDays = Math.max(Math.floor((action.payload.newSize - 340) / 110), 2);
      const numDaysOutOfBounds = action.payload.dayIdx - state.numDays - state.offset + 1;
      if (numDaysOutOfBounds > 0) {
        state.offset += numDaysOutOfBounds;
      }
    },
  },
});

export const {scrollNavbar, resizeWindow} = navigationSlice.actions;

export default navigationSlice.reducer;
