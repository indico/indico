// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const ADD_ERROR = 'ADD_ERROR';
export const CLEAR_ERROR = 'CLEAR_ERROR';
export const SHOW_REPORT_FORM = 'SHOW_REPORT_FORM';

export function addError(error) {
  return {
    type: ADD_ERROR,
    error: {
      title: error.title,
      message: error.message,
      errorUUID: error.error_uuid,
      reportable: !!error.error_uuid,
    },
  };
}

export function clearError() {
  return {type: CLEAR_ERROR};
}

export function showReportForm() {
  return {type: SHOW_REPORT_FORM};
}
