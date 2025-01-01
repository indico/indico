// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import * as actions from './actions';

const initialState = {
  errorList: [],
  formVisible: false,
};

export default function reducer(state = initialState, action) {
  switch (action.type) {
    case actions.ADD_ERROR:
      return {
        ...state,
        errorList: [...state.errorList, action.error],
      };
    case actions.CLEAR_ERROR:
      return {
        ...state,
        errorList: state.errorList.slice(1),
        formVisible: false,
      };
    case actions.SHOW_REPORT_FORM:
      return {
        ...state,
        formVisible: true,
      };
    default:
      return state;
  }
}
