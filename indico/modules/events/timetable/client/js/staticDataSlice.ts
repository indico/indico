// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSlice, PayloadAction} from '@reduxjs/toolkit';
import moment from 'moment';

interface StaticDataState {
  eventId: number;
  startDt: moment.Moment;
  endDt: moment.Moment;
}

const initialState: StaticDataState = {
  eventId: 0,
  startDt: moment(),
  endDt: moment(),
};

export const staticDataSlice = createSlice({
  name: 'staticData',
  initialState,
  reducers: {
    setStaticData: (state, action: PayloadAction<StaticDataState>) => {
      state = action.payload;
    },
  },
});

export const {setStaticData} = staticDataSlice.actions;

export default staticDataSlice.reducer;
