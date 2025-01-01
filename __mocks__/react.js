// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

/**
 * This module mocks some of React's hooks while providing
 * a way to tap into some of the internal methods (e.g. dispatch)
 */

import React from 'react';

const mockDispatches = [];

export * from 'react';

export function useReducer(reducer, initialState) {
  const [state, dispatch] = React.useReducer(reducer, initialState);
  const mockDispatch = jest.fn(action => {
    dispatch(action);
  });

  mockDispatches.push(mockDispatch);
  return [state, mockDispatch];
}

export function resetMocks() {
  while (mockDispatches.length) {
    mockDispatches.pop();
  }
}

export default {
  ...React,
  useReducer,
  resetMocks,
  mockDispatches,
};
