// This file is part of Indico.
// Copyright (C) 2002 - 2025 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

import {getItemById, getItems, getStaticData} from '../form/selectors';

export const getUserInfo = createSelector(
  getStaticData,
  staticData => staticData.userInfo
);

/** Indicates whether we are updating the registration */
export const getUpdateMode = createSelector(
  getStaticData,
  staticData => !!staticData.registrationUuid
);

/** Get the stored field values when editing a registration */
export const getRegistrationData = createSelector(
  getStaticData,
  staticData => staticData.registrationData
);

/** Indicates whether the registration is moderated */
export const getModeration = createSelector(
  getStaticData,
  staticData => staticData.moderated
);

/** Indicates whether this is rendered in the management area */
export const getManagement = createSelector(
  getStaticData,
  staticData => staticData.management || false
);

/** Indicates whether this registration has already been paid */
export const getPaid = createSelector(
  getStaticData,
  staticData => staticData.paid || false
);

/** Indicates whether the registration must be bound to a specific email */
export const getLockEmail = createSelector(
  getStaticData,
  staticData => staticData.lockEmail || false
);

/** Indicates the registration form's publishing to other participants mode */
export const getPublishToParticipants = createSelector(
  getStaticData,
  staticData => staticData.publishToParticipants
);

/** Indicates the registration form's public publishing mode */
export const getPublishToPublic = createSelector(
  getStaticData,
  staticData => staticData.publishToPublic
);

/** Get the stored value for a field when editing a registration */
export const getFieldValue = createSelector(
  getUpdateMode,
  getRegistrationData,
  (state, id) => getItemById(state, id),
  (updateMode, registrationData, field) =>
    updateMode ? registrationData[field.htmlName] : undefined
);

const getFieldsWithPrices = createSelector(
  getItems,
  fields =>
    new Set(
      Object.values(fields)
        .filter(field => field.price > 0 || field.choices?.some(c => c.price > 0))
        .map(field => field.id)
    )
);

export const isPaidItemLocked = createSelector(
  getPaid,
  (state, id) => getItemById(state, id),
  (state, id) => getFieldValue(state, id),
  getFieldsWithPrices,
  (paid, field, value, fieldsWithPrices) => {
    if (!paid) {
      // nothing locked if the registration hasn't been paid yet
      return false;
    } else if (field.price > 0) {
      // easy for fields that have a price themselves
      return true;
    } else if (value !== undefined && value !== null && field.choices) {
      // we assume that all fields with more complex options have them in `choices`,
      // and that a billable choice will have a `price`. if the old value is undefined,
      // we never disable the field altogether since some choices could in fact be free,
      // and we rely on the field to disable problematic choices
      let choiceIsSelected;
      if (typeof value === 'string') {
        choiceIsSelected = c => c.id === value;
      } else if (value.choice) {
        choiceIsSelected = c => c.id === value.choice;
      } else {
        choiceIsSelected = c => value[c.id] > 0;
      }
      if (field.choices.some(c => c.price > 0 && choiceIsSelected(c))) {
        return true;
      }
    }
    // check if the field is a condition for any field with a price. we do not look at the
    // actual condition to disable individual options here, since it's (hopefully) unlikely
    // enough that a registration form allows changes after payment and also wants to let
    // registrants change options (in a multi-choice field) that aren't conditions for a
    // field with a price.
    return !!new Set(field.showIfConditionForTransitive).intersection(fieldsWithPrices).size;
  }
);
