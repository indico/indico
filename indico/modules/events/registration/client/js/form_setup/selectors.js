// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

export const isUILocked = state => state.uiLocked;
export const getStaticData = state => state.staticData;
const getFlatSections = state => state.sections;
const getItems = state => state.items;

/** Get a sorted list of disabled sections. */
export const getDisabledSections = createSelector(
  getFlatSections,
  sections => _.sortBy(Object.values(sections).filter(s => !s.enabled), ['position', 'id'])
);

/** Get a sorted list of enabled top-level sections. */
const getSections = createSelector(
  getFlatSections,
  sections => _.sortBy(Object.values(sections).filter(s => s.enabled), ['position', 'id'])
);

/** Get a mapping from section IDs to sorted item lists. */
const getSectionItemMapping = createSelector(
  getFlatSections,
  getItems,
  (sections, fields) => {
    const mapping = new Map(Object.values(sections).map(s => [s.id, []]));
    _.sortBy(Object.values(fields), ['position', 'id']).forEach(field => {
      mapping.get(field.sectionId).push(field);
    });
    return mapping;
  }
);

/** Get the nested form structure of sections and their items. */
export const getNestedSections = createSelector(
  getSections,
  getSectionItemMapping,
  (sortedSections, sectionFields) =>
    sortedSections.map(section => ({
      ...section,
      items: sectionFields.get(section.id),
    }))
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

/** Get an item by its ID. */
export const getItemById = createSelector(
  getItems,
  (__, itemId) => itemId,
  (fields, itemId) => fields[itemId]
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
