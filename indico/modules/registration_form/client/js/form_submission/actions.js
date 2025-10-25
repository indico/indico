// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

export const SET_FORM_DATA = 'Set form data';
export const SET_HIDDEN_ITEM_IDS = 'Set hidden item ids';

export function setFormData(data) {
  return {type: SET_FORM_DATA, items: data.items, sections: data.sections};
}

export function setHiddenItemIds(hiddenItemIds) {
  return {type: SET_HIDDEN_ITEM_IDS, hiddenItemIds};
}
