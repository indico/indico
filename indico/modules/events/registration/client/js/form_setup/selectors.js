// This file is part of Indico.
// Copyright (C) 2002 - 2021 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import {createSelector} from 'reselect';

export const getSections = state => state.sections;

export const isUILocked = state => state.uiLocked;

const getItemIdSectionIdMapping = createSelector(
  getSections,
  sections => {
    const mapping = new Map();
    sections.forEach(section => {
      section.items.forEach(item => {
        mapping.set(item.id, section.id);
      });
    });
    return mapping;
  }
);

const getFlatItems = createSelector(
  getSections,
  sections => {
    const mapping = new Map();
    sections.forEach(section => {
      section.items.forEach(item => {
        mapping.set(item.id, item);
      });
    });
    return mapping;
  }
);

export const getSectionIdByItemId = createSelector(
  getItemIdSectionIdMapping,
  (_, itemId) => itemId,
  (mapping, itemId) => mapping.get(itemId)
);

const getItemById = createSelector(
  getFlatItems,
  (_, itemId) => itemId,
  (mapping, itemId) => mapping.get(itemId)
);

const isItemStaticText = createSelector(
  getItemById,
  item => item.inputType === 'label'
);

export const pickItemURL = createSelector(
  isItemStaticText,
  isStaticText => (textURL, fieldURL) => (isStaticText ? textURL : fieldURL)
);

export const getURLParams = createSelector(
  state => state.staticData,
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
