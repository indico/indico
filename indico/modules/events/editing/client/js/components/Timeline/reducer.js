// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {SET_LOADING, SET_DETAILS} from './actions';

export default function reducer(state, action) {
  switch (action.type) {
    case SET_LOADING:
      return {...state, isLoading: action.loading};
    case SET_DETAILS:
      return {...state, details: action.details};
    default:
      throw new Error();
  }
}
