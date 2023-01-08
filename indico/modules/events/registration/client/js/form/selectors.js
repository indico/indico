// This file is part of Indico.
// Copyright (C) 2002 - 2023 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import _ from 'lodash';
import {createSelector} from 'reselect';

export const getStaticData = state => state.staticData;

export const getFlatSections = state => state.sections;
export const getItems = state => state.items;

/** Get an item by its ID. */
export const getItemById = createSelector(
  getItems,
  (__, itemId) => itemId,
  (fields, itemId) => fields[itemId]
);

/** Get the currency used by the registration form. */
export const getCurrency = createSelector(
  getStaticData,
  staticData => staticData.currency
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
