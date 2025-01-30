// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSlice} from '@reduxjs/toolkit';

interface ExperimentalState {
  popupsEnabled: boolean;
}

const initialState: ExperimentalState = {
  popupsEnabled: false,
};

export const experimentalSlice = createSlice({
  name: 'experimental',
  initialState,
  reducers: {
    experimentalTogglePopups: state => {
      state.popupsEnabled = !state.popupsEnabled;
    },
  },
});

export const {experimentalTogglePopups} = experimentalSlice.actions;

export default experimentalSlice.reducer;
