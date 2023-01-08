// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

import {getStaticData, getFlatSections, getItems, getItemById} from '../form/selectors';

export const isUILocked = state => state.uiLocked;

/** Get a sorted list of disabled sections. */
export const getDisabledSections = createSelector(
  getFlatSections,
  sections => _.sortBy(Object.values(sections).filter(s => !s.enabled), ['position', 'id'])
);

/** Get a section by its ID. */
export const getSectionById = createSelector(
  getFlatSections,
  (__, sectionId) => sectionId,
  (sections, sectionId) => sections[sectionId]
);

/** Get the section ID for a given item ID. */
export const getSectionIdForItem = createSelector(
  getItems,
  (__, itemId) => itemId,
  (fields, itemId) => fields[itemId].sectionId
);

/** Check whether an item is a static text field. */
const isItemStaticText = createSelector(
  getItemById,
  item => item.inputType === 'label'
);

/** Select the correct URL for an item action dependin on whether it's static text or a field. */
export const pickItemURL = createSelector(
  isItemStaticText,
  isStaticText => (textURL, fieldURL) => (isStaticText ? textURL : fieldURL)
);

/** Get the URL path arguments for a regform/section/field operation. */
export const getURLParams = createSelector(
  getStaticData,
  staticData => {
    const {eventId, regformId} = staticData;
    return (sectionId = null, itemId = null) => {
      const params = {
        event_id: eventId,
        reg_form_id: regformId,
      };

      if (sectionId !== null) {
        params.section_id = sectionId;
      }

      if (itemId !== null) {
        params.field_id = itemId;
      }

      return params;
    };
  }
);
