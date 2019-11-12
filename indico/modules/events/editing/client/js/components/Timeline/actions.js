// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const SET_LOADING = 'SET_LOADING';
export const SET_DETAILS = 'SET_DETAILS';

export function setLoading(loading) {
  return {
    type: SET_LOADING,
    loading,
  };
}

export function setDetails(details) {
  return {
    type: SET_DETAILS,
    details,
  };
}
