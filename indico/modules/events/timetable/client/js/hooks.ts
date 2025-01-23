// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {useDispatch, useSelector, useStore, type TypedUseSelectorHook} from 'react-redux'

import type {TimetableDispatch, TimetableStore, RootState} from './store'

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useTimetableDispatch: () => TimetableDispatch = useDispatch;
export const useTimetableSelector: TypedUseSelectorHook<RootState> = useSelector;
export const useTimetableStore: () => TimetableStore = useStore;
