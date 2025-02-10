// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSlice, PayloadAction} from '@reduxjs/toolkit';

import {Entry} from './types';

interface OpenModalState {
  type: string | null; // TODO
  entry?: Entry;
}

const initialState: OpenModalState = {
  type: null,
  entry: null,
};

export const openModalSlice = createSlice({
  name: 'openModal',
  initialState,
  reducers: {
    addEntry: (state, action: PayloadAction<string>) => {
      state.type = action.payload;
      state.entry = null;
    },
    editEntry: (state, action: PayloadAction<{type: string; entry: Entry}>) => {
      state.type = action.payload.type;
      state.entry = action.payload.entry;
    },
    closeModal: state => {
      state.type = null;
      state.entry = null;
    },
  },
});

export const {addEntry, editEntry, closeModal} = openModalSlice.actions;

export default openModalSlice.reducer;
