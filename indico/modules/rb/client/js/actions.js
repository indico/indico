// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

// Page state
export const INIT = 'INIT';
export const RESET_PAGE_STATE = 'RESET_PAGE_STATE';
export const EXTEND_OVERRIDES = 'EXTEND_OVERRIDES';

export function init() {
  return {type: INIT};
}

export function resetPageState(namespace) {
  return {type: RESET_PAGE_STATE, namespace};
}

export function extendOverrides(overrides) {
  return {type: EXTEND_OVERRIDES, overrides};
}
